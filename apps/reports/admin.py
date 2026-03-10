from django.contrib import admin
from .models import DailyReport


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ('ad', 'date', 'impressions', 'clicks', 'ctr', 'spent')
    list_filter = ('date',)
    search_fields = ('ad__name',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
