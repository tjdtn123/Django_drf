from django.contrib import admin
from .models import EventLog


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ('ad', 'event_type', 'ip_address', 'device_type', 'created_at')
    list_filter = ('event_type', 'device_type', 'created_at')
    search_fields = ('ad__name', 'ip_address')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
