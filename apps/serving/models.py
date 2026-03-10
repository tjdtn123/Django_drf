from django.db import models
from apps.campaigns.models import Ad


class EventLog(models.Model):
    """이벤트 로그 모델 - 노출/클릭 이벤트 기록"""

    class EventType(models.TextChoices):
        IMPRESSION = 'impression', '노출'
        CLICK = 'click', '클릭'

    class DeviceType(models.TextChoices):
        PC = 'pc', 'PC'
        MOBILE = 'mobile', '모바일'
        TABLET = 'tablet', '태블릿'

    ad = models.ForeignKey(
        Ad, on_delete=models.CASCADE, related_name='event_logs', verbose_name='광고'
    )
    event_type = models.CharField(
        max_length=20, choices=EventType.choices, verbose_name='이벤트 유형'
    )
    ip_address = models.GenericIPAddressField(verbose_name='사용자 IP')
    user_agent = models.TextField(blank=True, verbose_name='User-Agent')
    device_type = models.CharField(
        max_length=10, choices=DeviceType.choices, default=DeviceType.PC, verbose_name='디바이스'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='이벤트 발생 시각')

    class Meta:
        verbose_name = '이벤트 로그'
        verbose_name_plural = '이벤트 로그 목록'
        indexes = [
            models.Index(fields=['ad', 'event_type', 'created_at']),
            models.Index(fields=['ip_address', 'ad']),
            # 일별 집계 쿼리 최적화: created_at__date 필터용
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'[{self.get_event_type_display()}] {self.ad.name} - {self.ip_address}'
