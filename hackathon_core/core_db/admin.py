from django.contrib import admin
from .models import AgentLog, SensorReading

@admin.register(AgentLog)
class AgentLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'machine_id', 'status', 'risk_score')
    list_filter = ('status',)

@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'machine_id', 'vibration', 'temperature')
    list_filter = ('machine_id',)
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
