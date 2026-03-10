from django.contrib import admin
from .models import Advertiser


@admin.register(Advertiser)
class AdvertiserAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'business_number', 'balance', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('company_name', 'user__username', 'business_number')
    readonly_fields = ('created_at',)
