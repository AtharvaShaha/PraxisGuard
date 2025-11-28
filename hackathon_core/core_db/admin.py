from django.contrib import admin
from .models import AgentLog

@admin.register(AgentLog)
class AgentLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'machine_id', 'status', 'risk_score')
    list_filter = ('status',)