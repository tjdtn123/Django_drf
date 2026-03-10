from django.db import models
from apps.campaigns.models import Ad


class DailyReport(models.Model):
    """일별 통계 모델 - Celery로 매일 집계"""

    ad = models.ForeignKey(
        Ad, on_delete=models.CASCADE, related_name='daily_reports', verbose_name='광고'
    )
    date = models.DateField(verbose_name='집계 날짜')
    impressions = models.IntegerField(default=0, verbose_name='노출수')
    clicks = models.IntegerField(default=0, verbose_name='클릭수')
    ctr = models.DecimalField(max_digits=5, decimal_places=4, default=0, verbose_name='CTR')
    spent = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='소진 광고비')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '일별 통계'
        verbose_name_plural = '일별 통계 목록'
        unique_together = ('ad', 'date')
        indexes = [
            models.Index(fields=['ad', 'date']),
        ]

    def __str__(self):
        return f'{self.ad.name} - {self.date} (노출: {self.impressions}, 클릭: {self.clicks})'
