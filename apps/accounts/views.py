from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AdvertiserSerializer, RegisterSerializer


class RegisterView(APIView):
    """광고주 회원가입"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "회원가입이 완료되었습니다."}, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """내 광고주 정보 조회"""

    def get(self, request):
        if not hasattr(request.user, 'advertiser'):
            return Response({"detail": "광고주 프로필이 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdvertiserSerializer(request.user.advertiser)
        return Response(serializer.data)
