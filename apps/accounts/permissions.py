from rest_framework.permissions import BasePermission


class IsAdvertiser(BasePermission):
    """Advertiser 프로필이 있는 인증된 사용자만 허용"""
    message = "광고주 계정이 필요합니다."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'advertiser')
        )


class IsOwnerAdvertiser(IsAdvertiser):
    """자신의 광고주 데이터만 접근 허용"""

    def has_object_permission(self, request, view, obj):
        # obj가 Campaign인 경우
        if hasattr(obj, 'advertiser'):
            return obj.advertiser.user == request.user
        # obj가 Ad인 경우
        if hasattr(obj, 'campaign'):
            return obj.campaign.advertiser.user == request.user
        return False
