"""
광고 서빙 API 테스트
"""
import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Advertiser
from apps.campaigns.models import Ad, Campaign, Creative, Inventory
from apps.serving.services import AdSelectionService


@pytest.fixture
def setup_active_ad(db):
    """활성 광고 1개 포함한 전체 셋업"""
    user = User.objects.create_user(username='adv', password='test1234!')
    advertiser = Advertiser.objects.create(user=user, company_name='테스트', business_number='000-00-00000')
    inventory = Inventory.objects.create(
        name='메인 배너', slot_code='main_banner', width=728, height=90
    )
    now = timezone.now()
    campaign = Campaign.objects.create(
        advertiser=advertiser, name='테스트 캠페인',
        status=Campaign.Status.ACTIVE,
        budget=1_000_000, daily_budget=100_000,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=30),
        billing_type='cpm', unit_price=1000,
    )
    ad = Ad.objects.create(
        campaign=campaign, inventory=inventory,
        name='테스트 광고', status=Ad.Status.ACTIVE, weight=100,
    )
    Creative.objects.create(
        ad=ad, file='creatives/test.jpg',
        click_url='https://example.com', alt_text='테스트 광고',
    )
    return ad


class TestAdServeAPI:

    def test_serve_returns_ad(self, setup_active_ad):
        client = APIClient()
        with patch('apps.serving.views.AdSelectionService') as MockService:
            mock_instance = MagicMock()
            mock_instance.select.return_value = setup_active_ad
            MockService.return_value = mock_instance

            response = client.get('/api/v1/serve/?slot=main_banner')
            assert response.status_code == 200
            assert 'ad_id' in response.data
            assert 'impression_url' in response.data
            assert 'click_url' in response.data

    def test_serve_missing_slot(self, db):
        client = APIClient()
        response = client.get('/api/v1/serve/')
        assert response.status_code == 400

    def test_impression_tracking(self, setup_active_ad):
        client = APIClient()
        ad = setup_active_ad
        response = client.get(f'/api/v1/track/impression/{ad.id}/')
        assert response.status_code == 200
        assert response['Content-Type'] == 'image/gif'

    def test_click_tracking_redirect(self, setup_active_ad):
        client = APIClient()
        ad = setup_active_ad
        redirect_url = 'https://example.com'
        response = client.get(f'/api/v1/track/click/{ad.id}/?redirect={redirect_url}')
        assert response.status_code == 302
        assert response['Location'] == redirect_url


class TestAdSelectionService:

    def test_no_inventory(self, db):
        service = AdSelectionService()
        result = service.select('nonexistent_slot', 'pc', '1.2.3.4')
        assert result is None

    def test_no_active_campaigns(self, db):
        Inventory.objects.create(
            name='빈 배너', slot_code='empty_banner', width=300, height=250
        )
        service = AdSelectionService()
        with patch.object(service, '_get_candidates', return_value=[]):
            result = service.select('empty_banner', 'pc', '1.2.3.4')
        assert result is None

    def test_targeting_hour_filter(self, db, setup_active_ad):
        ad = setup_active_ad
        ad.targeting = {'hours': [9, 10, 11]}
        ad.save()

        service = AdSelectionService()
        # 허용 시간대
        filtered = service._filter_by_targeting([ad], 'pc', 10)
        assert len(filtered) == 1
        # 비허용 시간대
        filtered = service._filter_by_targeting([ad], 'pc', 3)
        assert len(filtered) == 0

    def test_weighted_random_choice(self, db, setup_active_ad):
        """가중치 기반 선택 - 확률 검증"""
        ad = setup_active_ad
        ad.weight = 100
        ad.save()

        service = AdSelectionService()
        result = service._weighted_random_choice([ad])
        assert result == ad
