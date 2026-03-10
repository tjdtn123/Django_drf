from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AdViewSet, CampaignViewSet, InventoryViewSet

router = DefaultRouter()
router.register('', CampaignViewSet, basename='campaign')
router.register('inventories', InventoryViewSet, basename='inventory')
router.register('ads', AdViewSet, basename='ad')

urlpatterns = [
    path('', include(router.urls)),
]
