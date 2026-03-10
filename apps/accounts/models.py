from django.db import models
from django.contrib.auth.models import User


class Advertiser(models.Model):
    """광고주 계정 모델 (Django User 1:1 확장)"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='advertiser')
    company_name = models.CharField(max_length=100, verbose_name='회사명')
    business_number = models.CharField(max_length=20, verbose_name='사업자등록번호')
    balance = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, verbose_name='광고비 잔액'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일')

    class Meta:
        verbose_name = '광고주'
        verbose_name_plural = '광고주 목록'

    def __str__(self):
        return f'{self.company_name} ({self.user.username})'
