"""
Celery 태스크 - 통계 집계
Spring의 @Scheduled + @Async 역할을 Celery + Celery Beat으로 구현

스케줄:
  - aggregate_daily_stats: 매일 새벽 1시 (EventLog → DailyReport)
  - cleanup_old_event_logs: 매주 일요일 새벽 3시 (90일 이전 로그 삭제)
"""
import logging
from datetime import date, timedelta

from celery import shared_task
from django.db import transaction
from django.db.models import Count, Q, Sum

from apps.campaigns.models import Ad
from apps.serving.models import EventLog

from .models import DailyReport

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def aggregate_daily_stats(self, target_date_str: str = None):
    """
    EventLog → DailyReport 일별 집계 태스크
    target_date_str: 'YYYY-MM-DD' (None이면 어제 날짜)
    """
    try:
        if target_date_str:
            target_date = date.fromisoformat(target_date_str)
        else:
            target_date = date.today() - timedelta(days=1)

        logger.info(f"[aggregate_daily_stats] 집계 시작: {target_date}")

        # 해당 날짜에 이벤트가 있는 광고 ID 목록
        ad_ids = (
            EventLog.objects
            .filter(created_at__date=target_date)
            .values_list('ad_id', flat=True)
            .distinct()
        )

        updated = 0
        for ad_id in ad_ids:
            _aggregate_for_ad(ad_id, target_date)
            updated += 1

        logger.info(f"[aggregate_daily_stats] 완료: {target_date}, {updated}개 광고 집계")
        return {'date': str(target_date), 'updated': updated}

    except Exception as exc:
        logger.error(f"[aggregate_daily_stats] 실패: {exc}")
        raise self.retry(exc=exc, countdown=60)


@transaction.atomic
def _aggregate_for_ad(ad_id: int, target_date: date):
    """광고 1개의 일별 통계 집계 (트랜잭션 보장)"""
    logs = EventLog.objects.filter(ad_id=ad_id, created_at__date=target_date)

    impressions = logs.filter(event_type=EventLog.EventType.IMPRESSION).count()
    clicks = logs.filter(event_type=EventLog.EventType.CLICK).count()
    ctr = (clicks / impressions) if impressions > 0 else 0

    # 과금 계산
    try:
        ad = Ad.objects.select_related('campaign').get(pk=ad_id)
        campaign = ad.campaign
        if campaign.billing_type == 'cpm':
            spent = (impressions / 1000) * float(campaign.unit_price)
        elif campaign.billing_type == 'cpc':
            spent = clicks * float(campaign.unit_price)
        else:
            spent = 0
    except Ad.DoesNotExist:
        spent = 0

    DailyReport.objects.update_or_create(
        ad_id=ad_id,
        date=target_date,
        defaults={
            'impressions': impressions,
            'clicks': clicks,
            'ctr': round(ctr, 4),
            'spent': round(spent, 2),
        },
    )


@shared_task
def cleanup_old_event_logs(days: int = 90):
    """오래된 EventLog 삭제 (기본 90일 이전)"""
    cutoff = date.today() - timedelta(days=days)
    deleted_count, _ = EventLog.objects.filter(created_at__date__lt=cutoff).delete()
    logger.info(f"[cleanup_old_event_logs] {cutoff} 이전 로그 {deleted_count}건 삭제")
    return {'deleted': deleted_count}
