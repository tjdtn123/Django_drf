"""
리포트 API 및 통계 집계 테스트
"""
import pytest
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Advertiser
from apps.campaigns.models import Ad, Campaign, Inventory
from apps.reports.models import DailyReport
from apps.reports.services import ReportService
from apps.reports.tasks import aggregate_daily_stats, _aggregate_for_ad
from apps.serving.models import EventLog


@pytest.fixture
def full_setup(db):
    """캠페인 + 광고 + 이벤트 로그 전체 셋업"""
    user = User.objects.create_user(username='reporter', password='test1234!')
    advertiser = Advertiser.objects.create(
        user=user, company_name='리포트 테스트', business_number='000-00-00000'
    )
    inventory = Inventory.objects.create(
        name='배너', slot_code='report_banner', width=728, height=90
    )
    now = timezone.now()
    campaign = Campaign.objects.create(
        advertiser=advertiser, name='리포트 캠페인',
        status=Campaign.Status.ACTIVE,
        budget=1_000_000, daily_budget=100_000,
        start_date=now - timedelta(days=10),
        end_date=now + timedelta(days=20),
        billing_type='cpm', unit_price=1000,
    )
    ad = Ad.objects.create(
        campaign=campaign, inventory=inventory,
        name='리포트 광고', status=Ad.Status.ACTIVE, weight=100,
    )

    # 오늘 이벤트 로그 생성
    today = date.today()
    for _ in range(10):
        EventLog.objects.create(
            ad=ad, event_type=EventLog.EventType.IMPRESSION,
            ip_address='1.2.3.4', device_type='pc',
        )
    for _ in range(2):
        EventLog.objects.create(
            ad=ad, event_type=EventLog.EventType.CLICK,
            ip_address='1.2.3.4', device_type='pc',
        )

    return {'user': user, 'advertiser': advertiser, 'campaign': campaign, 'ad': ad}


@pytest.fixture
def auth_client(full_setup):
    client = APIClient()
    r = client.post('/api/v1/auth/token/', {'username': 'reporter', 'password': 'test1234!'})
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')
    return client, full_setup


class TestAggregation:

    def test_aggregate_for_ad(self, full_setup):
        """_aggregate_for_ad: EventLog → DailyReport 집계 정확성"""
        ad = full_setup['ad']
        today = date.today()

        _aggregate_for_ad(ad.id, today)

        report = DailyReport.objects.get(ad=ad, date=today)
        assert report.impressions == 10
        assert report.clicks == 2
        assert float(report.ctr) == 0.2  # 2/10
        # CPM 과금: 10 / 1000 * 1000 = 10원
        assert float(report.spent) == 10.0

    def test_aggregate_daily_stats_task(self, full_setup):
        """Celery 태스크 직접 실행 테스트"""
        today = date.today()
        result = aggregate_daily_stats(str(today))
        assert result['updated'] >= 1

    def test_aggregate_creates_report(self, full_setup):
        """집계 후 DailyReport가 생성되는지 확인"""
        ad = full_setup['ad']
        today = date.today()
        assert not DailyReport.objects.filter(ad=ad, date=today).exists()

        _aggregate_for_ad(ad.id, today)

        assert DailyReport.objects.filter(ad=ad, date=today).exists()

    def test_aggregate_updates_existing(self, full_setup):
        """재집계 시 update_or_create 동작 확인"""
        ad = full_setup['ad']
        today = date.today()

        _aggregate_for_ad(ad.id, today)
        _aggregate_for_ad(ad.id, today)  # 두 번 실행

        # 중복 생성 없이 업데이트만
        assert DailyReport.objects.filter(ad=ad, date=today).count() == 1


class TestReportService:

    def test_get_campaign_summary(self, full_setup):
        """캠페인 요약 통계"""
        campaign = full_setup['campaign']
        ad = full_setup['ad']
        today = date.today()

        # DailyReport 직접 생성
        DailyReport.objects.create(
            ad=ad, date=today,
            impressions=1000, clicks=50, ctr=0.05, spent=1000
        )

        service = ReportService()
        summary = service.get_campaign_summary(campaign)

        assert summary['impressions'] == 1000
        assert summary['clicks'] == 50
        assert summary['ctr'] == 0.05
        assert summary['spent'] == 1000.0
        assert summary['budget_spent_rate'] == 0.1  # 1000 / 1_000_000 * 100

    def test_get_campaign_daily_stats(self, full_setup):
        """캠페인 일별 통계 조회"""
        campaign = full_setup['campaign']
        ad = full_setup['ad']
        today = date.today()

        DailyReport.objects.create(
            ad=ad, date=today - timedelta(days=1),
            impressions=500, clicks=10, ctr=0.02, spent=500
        )
        DailyReport.objects.create(
            ad=ad, date=today,
            impressions=800, clicks=20, ctr=0.025, spent=800
        )

        service = ReportService()
        stats = service.get_campaign_daily_stats(
            campaign.id,
            today - timedelta(days=7),
            today,
        )

        assert len(stats) == 2
        assert stats[0]['impressions'] == 500
        assert stats[1]['impressions'] == 800

    def test_export_csv(self, full_setup):
        """CSV 익스포트 형식 확인"""
        campaign = full_setup['campaign']
        ad = full_setup['ad']
        today = date.today()
        DailyReport.objects.create(
            ad=ad, date=today, impressions=100, clicks=5, ctr=0.05, spent=100
        )

        service = ReportService()
        csv_str = service.export_campaign_csv(campaign, today, today)

        assert 'date' in csv_str
        assert 'impressions' in csv_str
        assert '100' in csv_str


class TestReportAPI:

    def test_dashboard(self, auth_client):
        client, setup = auth_client
        response = client.get('/api/v1/reports/dashboard/')
        assert response.status_code == 200
        assert 'total_campaigns' in response.data
        assert 'recent_7days' in response.data

    def test_campaign_report(self, auth_client):
        client, setup = auth_client
        campaign = setup['campaign']
        ad = setup['ad']
        DailyReport.objects.create(
            ad=ad, date=date.today(), impressions=100, clicks=5, ctr=0.05, spent=100
        )

        response = client.get(f'/api/v1/reports/campaign/{campaign.id}/')
        assert response.status_code == 200
        assert 'summary' in response.data
        assert 'daily_stats' in response.data

    def test_export_csv_download(self, auth_client):
        client, setup = auth_client
        campaign = setup['campaign']
        response = client.get(f'/api/v1/reports/export/?campaign_id={campaign.id}')
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']
        assert 'attachment' in response['Content-Disposition']

    def test_cannot_access_other_campaign_report(self, db):
        """다른 광고주 캠페인 리포트 접근 불가"""
        other_user = User.objects.create_user(username='other2', password='test1234!')
        other_adv = Advertiser.objects.create(
            user=other_user, company_name='남의 회사', business_number='333-33-33333'
        )
        now = timezone.now()
        other_campaign = Campaign.objects.create(
            advertiser=other_adv, name='남의 캠페인',
            budget=1000, daily_budget=100,
            start_date=now, end_date=now + timedelta(days=1),
            billing_type='cpm', unit_price=1000,
        )

        me = User.objects.create_user(username='me2', password='test1234!')
        Advertiser.objects.create(user=me, company_name='내 회사2', business_number='444-44-44444')
        client = APIClient()
        r = client.post('/api/v1/auth/token/', {'username': 'me2', 'password': 'test1234!'})
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')

        response = client.get(f'/api/v1/reports/campaign/{other_campaign.id}/')
        assert response.status_code == 403
