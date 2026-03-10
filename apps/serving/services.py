"""
광고 선택 서비스 (Ad Selection Service)
니트머스 Ad Server의 핵심 로직을 단순화하여 구현

선택 파이프라인:
  1. 슬롯 코드로 인벤토리 필터링
  2. active 상태 캠페인/광고 필터링
  3. 기간 필터링 (start_date <= now <= end_date)
  4. 일일 예산 필터링
  5. 타겟팅 필터링 (시간대, 디바이스)
  6. Frequency Cap 체크 (Redis)
  7. 가중치 기반 랜덤 선택 (Weighted Random)
"""
import random
from datetime import date

from django.core.cache import cache
from django.utils import timezone

from apps.campaigns.models import Ad, Campaign, Inventory


class AdSelectionService:

    CACHE_TTL = 300  # 광고 후보 캐시 5분
    FREQ_CAP_TTL = 86400  # Frequency Cap TTL 24시간

    def select(self, slot_code: str, device_type: str, user_ip: str) -> Ad | None:
        """
        광고 선택 메인 메서드
        반환값: 선택된 Ad 객체 또는 None (노출할 광고 없음)
        """
        # 1. 인벤토리 확인
        inventory = self._get_inventory(slot_code)
        if not inventory:
            return None

        # 2~4. 후보 광고 조회 (캐시 활용)
        cache_key = f'ad_candidates:{slot_code}'
        candidates = cache.get(cache_key)
        if candidates is None:
            candidates = self._get_candidates(inventory)
            cache.set(cache_key, candidates, self.CACHE_TTL)

        if not candidates:
            return None

        # 5. 타겟팅 필터링
        now = timezone.localtime()
        candidates = self._filter_by_targeting(candidates, device_type, now.hour)

        if not candidates:
            return None

        # 6. Frequency Cap 필터링
        candidates = self._filter_by_frequency_cap(candidates, user_ip)

        if not candidates:
            return None

        # 7. 가중치 기반 랜덤 선택
        return self._weighted_random_choice(candidates)

    def _get_inventory(self, slot_code: str) -> Inventory | None:
        try:
            return Inventory.objects.get(slot_code=slot_code, is_active=True)
        except Inventory.DoesNotExist:
            return None

    def _get_candidates(self, inventory: Inventory) -> list[Ad]:
        """활성 캠페인 + 광고 + 기간 + 예산 필터링"""
        now = timezone.now()
        today = date.today()

        ads = (
            Ad.objects
            .filter(
                inventory=inventory,
                status=Ad.Status.ACTIVE,
                campaign__status=Campaign.Status.ACTIVE,
                campaign__start_date__lte=now,
                campaign__end_date__gte=now,
            )
            .select_related('campaign', 'inventory')
            .prefetch_related('creatives')
        )

        # 일일 예산 필터: Redis 실시간 소진액 vs daily_budget 비교
        result = []
        for ad in ads:
            spent_today = self._get_daily_spent(ad.campaign_id, today)
            if spent_today < float(ad.campaign.daily_budget):
                result.append(ad)

        return result

    def _filter_by_targeting(self, candidates: list[Ad], device_type: str, hour: int) -> list[Ad]:
        """시간대/디바이스 타겟팅 필터"""
        result = []
        for ad in candidates:
            targeting = ad.targeting or {}

            # 시간대 타겟팅
            allowed_hours = targeting.get('hours')
            if allowed_hours and hour not in allowed_hours:
                continue

            # 디바이스 타겟팅
            allowed_devices = targeting.get('devices')
            if allowed_devices and device_type not in allowed_devices:
                continue

            result.append(ad)
        return result

    def _filter_by_frequency_cap(self, candidates: list[Ad], user_ip: str) -> list[Ad]:
        """Redis 기반 Frequency Cap 필터"""
        result = []
        for ad in candidates:
            if ad.frequency_cap is None:
                result.append(ad)
                continue

            key = f'freq_cap:{ad.id}:{user_ip}'
            count = cache.get(key, 0)
            if count < ad.frequency_cap:
                result.append(ad)

        return result

    def _weighted_random_choice(self, candidates: list[Ad]) -> Ad:
        """가중치 비례 랜덤 선택 (Weighted Random Sampling)"""
        weights = [ad.weight for ad in candidates]
        return random.choices(candidates, weights=weights, k=1)[0]

    def _get_daily_spent(self, campaign_id: int, today: date) -> float:
        """Redis에서 오늘 소진 광고비 조회"""
        key = f'daily_spent:{campaign_id}:{today}'
        return float(cache.get(key, 0))

    def record_impression(self, ad: Ad, user_ip: str):
        """노출 카운터 증가 + Frequency Cap 업데이트"""
        # Redis 실시간 카운터
        imp_key = f'impressions:{ad.id}:{date.today()}'
        cache.incr(imp_key) if cache.get(imp_key) else cache.set(imp_key, 1, 86400)

        # Frequency Cap 카운터
        if ad.frequency_cap:
            freq_key = f'freq_cap:{ad.id}:{user_ip}'
            current = cache.get(freq_key, 0)
            cache.set(freq_key, current + 1, self.FREQ_CAP_TTL)

        # 일일 예산 소진액 업데이트 (CPM: 1,000회당 unit_price)
        campaign = ad.campaign
        if campaign.billing_type == 'cpm':
            cost = float(campaign.unit_price) / 1000
            self._add_daily_spent(campaign.id, cost)

    def record_click(self, ad: Ad):
        """클릭 카운터 증가 + CPC 과금"""
        click_key = f'clicks:{ad.id}:{date.today()}'
        cache.incr(click_key) if cache.get(click_key) else cache.set(click_key, 1, 86400)

        campaign = ad.campaign
        if campaign.billing_type == 'cpc':
            self._add_daily_spent(campaign.id, float(campaign.unit_price))

    def _add_daily_spent(self, campaign_id: int, amount: float):
        key = f'daily_spent:{campaign_id}:{date.today()}'
        current = float(cache.get(key, 0))
        cache.set(key, current + amount, 86400)
