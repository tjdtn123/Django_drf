from django.urls import path

from .views import CampaignReportView, DashboardView, ReportExportView, TriggerAggregationView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('campaign/<int:campaign_id>/', CampaignReportView.as_view(), name='campaign-report'),
    path('export/', ReportExportView.as_view(), name='report-export'),
    path('aggregate/', TriggerAggregationView.as_view(), name='trigger-aggregation'),
]
