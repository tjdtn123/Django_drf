from datetime import date, timedelta

from django.http import HttpResponse
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdvertiser
from apps.campaigns.models import Campaign
from apps.reports.tasks import aggregate_daily_stats

from .serializers import CampaignSummarySerializer, DailyStatSerializer, DashboardSerializer
from .services import ReportService


def _parse_date_params(request) -> tuple[date, date]:
    """쿼리 파라미터에서 start/end date 파싱 (기본: 최근 30일)"""
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    if request.query_params.get('start_date'):
        start_date = date.fromisoformat(request.query_params['start_date'])
    if request.query_params.get('end_date'):
        end_date = date.fromisoformat(request.query_params['end_date'])

    return start_date, end_date


class CampaignReportView(APIView):
    """
    캠페인별 일별 통계 조회
    GET /api/v1/reports/campaign/{id}/?start_date=2024-01-01&end_date=2024-01-31
    """
    permission_classes = [IsAdvertiser]

    def get(self, request, campaign_id):
        try:
            campaign = Campaign.objects.get(pk=campaign_id)
        except Campaign.DoesNotExist:
            raise NotFound("캠페인을 찾을 수 없습니다.")

        if campaign.advertiser.user != request.user:
            raise PermissionDenied("접근 권한이 없습니다.")

        start_date, end_date = _parse_date_params(request)
        service = ReportService()
        stats = service.get_campaign_daily_stats(campaign_id, start_date, end_date)
        summary = service.get_campaign_summary(campaign)

        return Response({
            'summary': CampaignSummarySerializer(summary).data,
            'daily_stats': DailyStatSerializer(stats, many=True).data,
        })


class DashboardView(APIView):
    """
    광고주 대시보드 요약
    GET /api/v1/reports/dashboard/
    """
    permission_classes = [IsAdvertiser]

    def get(self, request):
        service = ReportService()
        data = service.get_advertiser_dashboard(request.user.advertiser)
        return Response(DashboardSerializer(data).data)


class ReportExportView(APIView):
    """
    캠페인 통계 CSV 다운로드
    GET /api/v1/reports/export/?campaign_id=1&start_date=...&end_date=...
    """
    permission_classes = [IsAdvertiser]

    def get(self, request):
        campaign_id = request.query_params.get('campaign_id')
        if not campaign_id:
            return Response({"detail": "campaign_id 파라미터가 필요합니다."}, status=400)

        try:
            campaign = Campaign.objects.get(pk=campaign_id)
        except Campaign.DoesNotExist:
            raise NotFound("캠페인을 찾을 수 없습니다.")

        if campaign.advertiser.user != request.user:
            raise PermissionDenied("접근 권한이 없습니다.")

        start_date, end_date = _parse_date_params(request)
        service = ReportService()
        csv_content = service.export_campaign_csv(campaign, start_date, end_date)

        filename = f"campaign_{campaign_id}_{start_date}_{end_date}.csv"
        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class TriggerAggregationView(APIView):
    """
    수동 통계 집계 트리거 (개발/테스트용)
    POST /api/v1/reports/aggregate/
    body: {"date": "2024-01-15"}  (선택)
    """
    permission_classes = [IsAdvertiser]

    def post(self, request):
        target_date = request.data.get('date')
        # Celery 태스크 비동기 실행
        task = aggregate_daily_stats.delay(target_date)
        return Response({
            "message": "집계 태스크가 시작되었습니다.",
            "task_id": task.id,
        })
