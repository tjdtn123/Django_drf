from django.contrib import admin
from .models import Campaign, Inventory, Ad, Creative


class AdInline(admin.TabularInline):
    model = Ad
    extra = 0
    fields = ('name', 'inventory', 'status', 'weight', 'frequency_cap')


class CreativeInline(admin.TabularInline):
    model = Creative
    extra = 0
    fields = ('file', 'click_url', 'alt_text', 'is_active')


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'advertiser', 'status', 'billing_type', 'budget', 'start_date', 'end_date')
    list_filter = ('status', 'billing_type')
    search_fields = ('name', 'advertiser__company_name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AdInline]
    actions = ['activate_campaigns', 'pause_campaigns']

    @admin.action(description='선택 캠페인 활성화')
    def activate_campaigns(self, request, queryset):
        queryset.update(status=Campaign.Status.ACTIVE)

    @admin.action(description='선택 캠페인 일시정지')
    def pause_campaigns(self, request, queryset):
        queryset.update(status=Campaign.Status.PAUSED)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slot_code', 'media_type', 'width', 'height', 'is_active')
    list_filter = ('media_type', 'is_active')
    search_fields = ('name', 'slot_code')


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ('name', 'campaign', 'inventory', 'status', 'weight', 'frequency_cap')
    list_filter = ('status',)
    search_fields = ('name', 'campaign__name')
    inlines = [CreativeInline]


@admin.register(Creative)
class CreativeAdmin(admin.ModelAdmin):
    list_display = ('ad', 'click_url', 'alt_text', 'is_active', 'created_at')
    list_filter = ('is_active',)
