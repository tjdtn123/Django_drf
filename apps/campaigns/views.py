from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsAdvertiser, IsOwnerAdvertiser

from .models import Ad, Campaign, Creative, Inventory
from .serializers import (
    AdListSerializer,
    AdSerializer,
    CampaignListSerializer,
    CampaignSerializer,
    CreativeSerializer,
    InventorySerializer,
)


class CampaignViewSet(ModelViewSet):
    """
    캠페인 CRUD + activate/pause 액션
    Spring의 @RestController + @Service 역할을 ViewSet 하나로 처리
    """
    permission_classes = [IsAdvertiser, IsOwnerAdvertiser]

    def get_queryset(self):
        # 자신의 캠페인만 반환 (광고주 데이터 격리)
        return (
            Campaign.objects
            .filter(advertiser=self.request.user.advertiser)
            .select_related('advertiser__user')
            .prefetch_related('ads__inventory')
            .order_by('-created_at')
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return CampaignListSerializer
        return CampaignSerializer

    def perform_create(self, serializer):
        # advertiser는 현재 로그인 사용자로 자동 설정
        serializer.save(advertiser=self.request.user.advertiser)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status == Campaign.Status.COMPLETED:
            return Response(
                {"detail": "완료된 캠페인은 활성화할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        campaign.status = Campaign.Status.ACTIVE
        campaign.save(update_fields=['status'])
        return Response({"status": "active", "message": "캠페인이 활성화되었습니다."})

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status != Campaign.Status.ACTIVE:
            return Response(
                {"detail": "활성 상태의 캠페인만 일시정지할 수 있습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        campaign.status = Campaign.Status.PAUSED
        campaign.save(update_fields=['status'])
        return Response({"status": "paused", "message": "캠페인이 일시정지되었습니다."})


class InventoryViewSet(ModelViewSet):
    """인벤토리(지면) 관리 - 관리자만 생성/수정, 광고주는 목록 조회만"""
    queryset = Inventory.objects.filter(is_active=True)
    serializer_class = InventorySerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAdvertiser()]
        return [IsAdvertiser()]  # TODO: 관리자 권한으로 교체


class AdViewSet(ModelViewSet):
    """광고 CRUD"""
    permission_classes = [IsAdvertiser, IsOwnerAdvertiser]

    def get_queryset(self):
        return (
            Ad.objects
            .filter(campaign__advertiser=self.request.user.advertiser)
            .select_related('campaign', 'inventory')
            .prefetch_related('creatives')
            .order_by('-created_at')
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return AdListSerializer
        return AdSerializer

    @action(detail=True, methods=['post'], url_path='creatives')
    def upload_creative(self, request, pk=None):
        """소재 업로드"""
        ad = self.get_object()
        serializer = CreativeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(ad=ad)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
