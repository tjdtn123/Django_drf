import base64

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.campaigns.models import Ad

from .models import EventLog
from .services import AdSelectionService
from .utils import get_client_ip, get_device_type

# 1x1 투명 GIF (트래킹 픽셀)
TRACKING_PIXEL = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


class AdServeView(APIView):
    """
    광고 서빙 API (★ 핵심)
    GET /api/v1/serve/?slot=main_banner&device=pc

    외부 매체가 호출 → 타겟 조건에 맞는 광고 JSON 반환
    """
    permission_classes = [AllowAny]

    def get(self, request):
        slot_code = request.query_params.get('slot')
        if not slot_code:
            return Response({"detail": "slot 파라미터가 필요합니다."}, status=400)

        user_ip = get_client_ip(request)
        device_type = request.query_params.get('device') or get_device_type(
            request.META.get('HTTP_USER_AGENT', '')
        )

        service = AdSelectionService()
        ad = service.select(slot_code=slot_code, device_type=device_type, user_ip=user_ip)

        if ad is None:
            return Response({"detail": "노출 가능한 광고가 없습니다."}, status=204)

        creative = ad.creatives.filter(is_active=True).first()
        if not creative:
            return Response({"detail": "활성 소재가 없습니다."}, status=204)

        base_url = request.build_absolute_uri('/')[:-1]
        return Response({
            "ad_id": ad.id,
            "creative_url": base_url + creative.file.url if creative.file else None,
            "click_url": f"{base_url}/api/v1/track/click/{ad.id}/?redirect={creative.click_url}",
            "impression_url": f"{base_url}/api/v1/track/impression/{ad.id}/",
            "width": ad.inventory.width,
            "height": ad.inventory.height,
            "alt_text": creative.alt_text,
        })


class ImpressionTrackView(APIView):
    """
    노출 트래킹 - 1x1 투명 GIF 반환
    GET /api/v1/track/impression/{ad_id}/
    """
    permission_classes = [AllowAny]

    def get(self, request, ad_id):
        ad = get_object_or_404(Ad, pk=ad_id)
        user_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_type = get_device_type(user_agent)

        # EventLog 기록
        EventLog.objects.create(
            ad=ad,
            event_type=EventLog.EventType.IMPRESSION,
            ip_address=user_ip,
            user_agent=user_agent,
            device_type=device_type,
        )

        # Redis 카운터 + Frequency Cap 업데이트
        AdSelectionService().record_impression(ad, user_ip)

        return HttpResponse(TRACKING_PIXEL, content_type='image/gif')


class ClickTrackView(APIView):
    """
    클릭 트래킹 + 302 리다이렉트
    GET /api/v1/track/click/{ad_id}/?redirect=https://...
    """
    permission_classes = [AllowAny]

    def get(self, request, ad_id):
        ad = get_object_or_404(Ad, pk=ad_id)
        redirect_url = request.query_params.get('redirect', '/')
        user_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        EventLog.objects.create(
            ad=ad,
            event_type=EventLog.EventType.CLICK,
            ip_address=user_ip,
            user_agent=user_agent,
            device_type=get_device_type(user_agent),
        )

        AdSelectionService().record_click(ad)

        return HttpResponseRedirect(redirect_url)
