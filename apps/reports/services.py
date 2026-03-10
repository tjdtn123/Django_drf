"""
리포트/통계 서비스
- 캠페인별 일별 통계 조회
- 대시보드 요약 (목표 대비 현황, 예산 소진율)
- CSV 익스포트
"""
import csv
import io
from datetime import date, timedelta

from django.db.models import Avg, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate

from apps.accounts.models import Advertiser
from apps.campaigns.models import Campaign
from apps.serving.models import EventLog

from .models import DailyReport


class ReportService:

    def get_campaign_daily_stats(
        self, campaign_id: int, start_date: date, end_date: date
    ) -> list[dict]:
        """캠페인 하위 전체 광고의 일별 통계 합계"""
        rows = (
            DailyReport.objects
            .filter(
                ad__campaign_id=campaign_id,
                date__range=(start_date, end_date),
            )
            .values('date')
            .annotate(
                total_impressions=Sum('impressions'),
                total_clicks=Sum('clicks'),
                total_spent=Sum('spent'),
            )
            .order_by('date')
        )
        result = []
        for row in rows:
            impressions = row['total_impressions'] or 0
            clicks = row['total_clicks'] or 0
            result.append({
                'date': row['date'],
                'impressions': impressions,
                'clicks': clicks,
                'ctr': round(clicks / impressions, 4) if impressions > 0 else 0,
                'spent': float(row['total_spent'] or 0),
            })
        return result

    def get_campaign_summary(self, campaign: Campaign) -> dict:
        """캠페인 요약: 목표 노출 달성률, 예산 소진율"""
        totals = DailyReport.objects.filter(ad__campaign=campaign).aggregate(
            total_impressions=Sum('impressions'),
            total_clicks=Sum('clicks'),
            total_spent=Sum('spent'),
        )
        impressions = totals['total_impressions'] or 0
        clicks = totals['total_clicks'] or 0
        spent = float(totals['total_spent'] or 0)
        budget = float(campaign.budget)

        return {
            'campaign_id': campaign.id,
            'campaign_name': campaign.name,
            'status': campaign.status,
            'impressions': impressions,
            'clicks': clicks,
            'ctr': round(clicks / impressions, 4) if impressions > 0 else 0,
            'spent': spent,
            'budget': budget,
            'budget_spent_rate': round(spent / budget * 100, 1) if budget > 0 else 0,
            'impression_achievement_rate': (
                round(impressions / campaign.target_impressions * 100, 1)
                if campaign.target_impressions > 0 else None
            ),
        }

    def get_advertiser_dashboard(self, advertiser: Advertiser) -> dict:
        """광고주 대시보드 요약"""
        campaigns = Campaign.objects.filter(advertiser=advertiser)
        active_campaigns = campaigns.filter(status=Campaign.Status.ACTIVE)

        # 최근 7일 통계
        seven_days_ago = date.today() - timedelta(days=7)
        recent_stats = DailyReport.objects.filter(
            ad__campaign__advertiser=advertiser,
            date__gte=seven_days_ago,
        ).aggregate(
            total_impressions=Sum('impressions'),
            total_clicks=Sum('clicks'),
            total_spent=Sum('spent'),
        )

        impressions = recent_stats['total_impressions'] or 0
        clicks = recent_stats['total_clicks'] or 0

        return {
            'total_campaigns': campaigns.count(),
            'active_campaigns': active_campaigns.count(),
            'recent_7days': {
                'impressions': impressions,
                'clicks': clicks,
                'ctr': round(clicks / impressions, 4) if impressions > 0 else 0,
                'spent': float(recent_stats['total_spent'] or 0),
            },
            'campaigns': [self.get_campaign_summary(c) for c in active_campaigns],
        }

    def export_campaign_csv(self, campaign: Campaign, start_date: date, end_date: date) -> str:
        """캠페인 통계 CSV 생성, 문자열 반환"""
        rows = self.get_campaign_daily_stats(campaign.id, start_date, end_date)

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=['date', 'impressions', 'clicks', 'ctr', 'spent'],
            extrasaction='ignore',
        )
        writer.writeheader()

        total_impressions = total_clicks = total_spent = 0
        for row in rows:
            writer.writerow({
                'date': row['date'],
                'impressions': row['impressions'],
                'clicks': row['clicks'],
                'ctr': f"{row['ctr']:.4f}",
                'spent': f"{row['spent']:.2f}",
            })
            total_impressions += row['impressions']
            total_clicks += row['clicks']
            total_spent += row['spent']

        # 합계 행
        writer.writerow({
            'date': '합계',
            'impressions': total_impressions,
            'clicks': total_clicks,
            'ctr': f"{(total_clicks / total_impressions):.4f}" if total_impressions > 0 else '0.0000',
            'spent': f"{total_spent:.2f}",
        })
        return output.getvalue()
