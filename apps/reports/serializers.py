from rest_framework import serializers

from .models import DailyReport


class DailyReportSerializer(serializers.ModelSerializer):
    ad_name = serializers.CharField(source='ad.name', read_only=True)
    campaign_name = serializers.CharField(source='ad.campaign.name', read_only=True)

    class Meta:
        model = DailyReport
        fields = ('id', 'ad', 'ad_name', 'campaign_name', 'date',
                  'impressions', 'clicks', 'ctr', 'spent')


class DailyStatSerializer(serializers.Serializer):
    """일별 집계 통계 (DailyReport 집계 결과)"""
    date = serializers.DateField()
    impressions = serializers.IntegerField()
    clicks = serializers.IntegerField()
    ctr = serializers.FloatField()
    spent = serializers.FloatField()


class CampaignSummarySerializer(serializers.Serializer):
    """캠페인 요약 통계"""
    campaign_id = serializers.IntegerField()
    campaign_name = serializers.CharField()
    status = serializers.CharField()
    impressions = serializers.IntegerField()
    clicks = serializers.IntegerField()
    ctr = serializers.FloatField()
    spent = serializers.FloatField()
    budget = serializers.FloatField()
    budget_spent_rate = serializers.FloatField()
    impression_achievement_rate = serializers.FloatField(allow_null=True)


class DashboardSerializer(serializers.Serializer):
    """대시보드 요약"""
    total_campaigns = serializers.IntegerField()
    active_campaigns = serializers.IntegerField()
    recent_7days = serializers.DictField()
    campaigns = CampaignSummarySerializer(many=True)
