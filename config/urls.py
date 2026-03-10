from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.accounts.dashboard_views import (
    login_view, dashboard_view, campaign_list_view, campaign_detail_view
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # 대시보드 UI
    path('', login_view, name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('dashboard/campaigns/', campaign_list_view, name='campaign-list'),
    path('dashboard/campaigns/<int:campaign_id>/', campaign_detail_view, name='campaign-detail'),

    # API v1
    path('api/v1/campaigns/', include('apps.campaigns.urls')),
    path('api/v1/', include('apps.serving.urls')),
    path('api/v1/reports/', include('apps.reports.urls')),
    path('api/v1/auth/', include('apps.accounts.urls')),

    # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
