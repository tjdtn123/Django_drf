from django.urls import path

from .views import AdServeView, ClickTrackView, ImpressionTrackView

urlpatterns = [
    path('serve/', AdServeView.as_view(), name='ad-serve'),
    path('track/impression/<int:ad_id>/', ImpressionTrackView.as_view(), name='track-impression'),
    path('track/click/<int:ad_id>/', ClickTrackView.as_view(), name='track-click'),
]
