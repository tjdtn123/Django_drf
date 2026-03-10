"""
캠페인 API 테스트
Spring의 @SpringBootTest + MockMvc 역할을 pytest-django + APIClient로 대체
"""
import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient

from apps.accounts.models import Advertiser
from apps.campaigns.models import Campaign, Inventory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def advertiser_user(db):
    user = User.objects.create_user(username='testuser', password='test1234!')
    advertiser = Advertiser.objects.create(
        user=user, company_name='테스트 회사', business_number='000-00-00000', balance=1_000_000
    )
    return user, advertiser


@pytest.fixture
def auth_client(api_client, advertiser_user):
    user, _ = advertiser_user
    response = api_client.post('/api/v1/auth/token/', {'username': 'testuser', 'password': 'test1234!'})
    token = response.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client


@pytest.fixture
def inventory(db):
    return Inventory.objects.create(
        name='테스트 배너', slot_code='test_banner', width=728, height=90, media_type='web'
    )


@pytest.fixture
def campaign(db, advertiser_user, inventory):
    _, advertiser = advertiser_user
    now = timezone.now()
    return Campaign.objects.create(
        advertiser=advertiser,
        name='테스트 캠페인',
        status=Campaign.Status.DRAFT,
        budget=1_000_000,
        daily_budget=100_000,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=30),
        billing_type=Campaign.BillingType.CPM,
        unit_price=1000,
    )


class TestCampaignAPI:

    def test_list_campaigns(self, auth_client, campaign):
        response = auth_client.get('/api/v1/campaigns/')
        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_create_campaign(self, auth_client, inventory):
        now = timezone.now()
        data = {
            'name': '새 캠페인',
            'budget': '500000.00',
            'daily_budget': '50000.00',
            'start_date': (now + timedelta(days=1)).isoformat(),
            'end_date': (now + timedelta(days=30)).isoformat(),
            'billing_type': 'cpm',
            'unit_price': '1000.00',
        }
        response = auth_client.post('/api/v1/campaigns/', data, format='json')
        assert response.status_code == 201
        assert response.data['name'] == '새 캠페인'

    def test_activate_campaign(self, auth_client, campaign):
        response = auth_client.post(f'/api/v1/campaigns/{campaign.id}/activate/')
        assert response.status_code == 200
        campaign.refresh_from_db()
        assert campaign.status == Campaign.Status.ACTIVE

    def test_pause_campaign(self, auth_client, campaign):
        campaign.status = Campaign.Status.ACTIVE
        campaign.save()
        response = auth_client.post(f'/api/v1/campaigns/{campaign.id}/pause/')
        assert response.status_code == 200
        campaign.refresh_from_db()
        assert campaign.status == Campaign.Status.PAUSED

    def test_cannot_access_other_campaign(self, db, inventory):
        """다른 광고주의 캠페인은 접근 불가"""
        other_user = User.objects.create_user(username='other', password='test1234!')
        other_adv = Advertiser.objects.create(
            user=other_user, company_name='다른 회사', business_number='111-11-11111'
        )
        now = timezone.now()
        other_campaign = Campaign.objects.create(
            advertiser=other_adv, name='다른 캠페인',
            budget=1000, daily_budget=100,
            start_date=now, end_date=now + timedelta(days=1),
            billing_type='cpm', unit_price=1000,
        )

        # testuser로 로그인
        client = APIClient()
        me = User.objects.create_user(username='me', password='test1234!')
        Advertiser.objects.create(user=me, company_name='내 회사', business_number='222-22-22222')
        r = client.post('/api/v1/auth/token/', {'username': 'me', 'password': 'test1234!'})
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')

        response = client.get(f'/api/v1/campaigns/{other_campaign.id}/')
        assert response.status_code == 404


class TestAuthAPI:

    def test_register(self, api_client, db):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'company_name': '신규 회사',
            'business_number': '999-99-99999',
        }
        response = api_client.post('/api/v1/auth/register/', data)
        assert response.status_code == 201

    def test_login(self, api_client, advertiser_user):
        response = api_client.post('/api/v1/auth/token/', {'username': 'testuser', 'password': 'test1234!'})
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_unauthenticated_access(self, api_client, db):
        response = api_client.get('/api/v1/campaigns/')
        assert response.status_code == 401
