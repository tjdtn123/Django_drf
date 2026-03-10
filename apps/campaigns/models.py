from django.db import models
from apps.accounts.models import Advertiser


class Campaign(models.Model):
    """캠페인 모델 - 광고 집행의 최상위 단위"""

    class Status(models.TextChoices):
        DRAFT = 'draft', '초안'
        ACTIVE = 'active', '활성'
        PAUSED = 'paused', '일시정지'
        COMPLETED = 'completed', '완료'

    class BillingType(models.TextChoices):
        CPM = 'cpm', 'CPM (1,000회 노출당 과금)'
        CPC = 'cpc', 'CPC (클릭당 과금)'
        CPP = 'cpp', 'CPP (기간당 고정)'
        CPV = 'cpv', 'CPV (동영상 조회당 과금)'

    advertiser = models.ForeignKey(
        Advertiser, on_delete=models.CASCADE, related_name='campaigns', verbose_name='광고주'
    )
    name = models.CharField(max_length=200, verbose_name='캠페인명')
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, verbose_name='상태'
    )
    budget = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='총 예산')
    daily_budget = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='일일 예산')
    start_date = models.DateTimeField(verbose_name='시작일')
    end_date = models.DateTimeField(verbose_name='종료일')
    target_impressions = models.IntegerField(default=0, verbose_name='목표 노출수')
    billing_type = models.CharField(
        max_length=10, choices=BillingType.choices, default=BillingType.CPM, verbose_name='과금 방식'
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='단가')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '캠페인'
        verbose_name_plural = '캠페인 목록'
        indexes = [
            models.Index(fields=['status', 'start_date', 'end_date']),
        ]

    def __str__(self):
        return f'[{self.get_status_display()}] {self.name}'


class Inventory(models.Model):
    """인벤토리(지면) 모델 - 광고가 노출되는 위치"""

    class MediaType(models.TextChoices):
        WEB = 'web', '웹'
        MOBILE = 'mobile', '모바일'
        VIDEO = 'video', '동영상'
        INAPP = 'inapp', '인앱'

    name = models.CharField(max_length=100, verbose_name='지면명')
    slot_code = models.SlugField(unique=True, verbose_name='슬롯 코드')
    width = models.IntegerField(verbose_name='너비(px)')
    height = models.IntegerField(verbose_name='높이(px)')
    media_type = models.CharField(
        max_length=10, choices=MediaType.choices, default=MediaType.WEB, verbose_name='매체 유형'
    )
    is_active = models.BooleanField(default=True, verbose_name='활성 여부')

    class Meta:
        verbose_name = '인벤토리(지면)'
        verbose_name_plural = '인벤토리(지면) 목록'

    def __str__(self):
        return f'{self.name} ({self.slot_code})'


class Ad(models.Model):
    """광고 모델 - 캠페인 하위 개별 광고 단위"""

    class Status(models.TextChoices):
        ACTIVE = 'active', '활성'
        PAUSED = 'paused', '일시정지'
        ENDED = 'ended', '종료'

    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name='ads', verbose_name='캠페인'
    )
    inventory = models.ForeignKey(
        Inventory, on_delete=models.CASCADE, related_name='ads', verbose_name='타겟 지면'
    )
    name = models.CharField(max_length=200, verbose_name='광고명')
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name='상태'
    )
    weight = models.IntegerField(default=100, verbose_name='노출 가중치(1~100)')
    frequency_cap = models.IntegerField(null=True, blank=True, verbose_name='빈도 제한(일 기준)')
    targeting = models.JSONField(default=dict, blank=True, verbose_name='타겟팅 설정')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '광고'
        verbose_name_plural = '광고 목록'
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.name} (가중치: {self.weight})'


class Creative(models.Model):
    """소재 모델 - 광고에 사용되는 이미지/동영상"""

    ad = models.ForeignKey(
        Ad, on_delete=models.CASCADE, related_name='creatives', verbose_name='광고'
    )
    file = models.FileField(upload_to='creatives/%Y/%m/', verbose_name='소재 파일')
    click_url = models.URLField(verbose_name='클릭 URL')
    alt_text = models.CharField(max_length=200, blank=True, verbose_name='대체 텍스트')
    is_active = models.BooleanField(default=True, verbose_name='활성 여부')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '소재'
        verbose_name_plural = '소재 목록'

    def __str__(self):
        return f'소재({self.ad.name}) - {self.file.name}'
