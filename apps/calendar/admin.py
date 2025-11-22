"""
Admin configuration for calendar app.
"""

from django.contrib import admin
from .models import (
    WorkingHours, TimeSlot, ClientAvailability, VisitSchedule,
    CalendarConflict, SchedulingPreference, ScheduleMetrics
)


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    """Admin for WorkingHours model."""
    list_display = ['user', 'day_of_week', 'start_time', 'end_time', 'is_working', 'is_active']
    list_filter = ['day_of_week', 'is_working', 'is_active']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    """Admin for TimeSlot model."""
    list_display = ['user', 'date', 'start_time', 'end_time', 'status']
    list_filter = ['status', 'date']
    search_fields = ['user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ClientAvailability)
class ClientAvailabilityAdmin(admin.ModelAdmin):
    """Admin for ClientAvailability model."""
    list_display = ['user', 'preferred_date', 'preferred_time_slot', 'urgency', 'is_active']
    list_filter = ['preferred_time_slot', 'urgency', 'is_active', 'preferred_date']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(VisitSchedule)
class VisitScheduleAdmin(admin.ModelAdmin):
    """Admin for VisitSchedule model."""
    list_display = ['property', 'client', 'agent', 'scheduled_date', 'scheduled_start_time', 'status', 'priority']
    list_filter = ['status', 'priority', 'matching_algorithm', 'scheduled_date']
    search_fields = ['property__title', 'client__username', 'agent__username']
    readonly_fields = ['id', 'match_score', 'confirmed_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('property', 'client', 'agent', 'reservation')
        }),
        ('Planification', {
            'fields': ('scheduled_date', 'scheduled_start_time', 'scheduled_end_time', 'status', 'priority')
        }),
        ('Algorithme et correspondance', {
            'fields': ('matching_algorithm', 'match_score', 'match_factors')
        }),
        ('Transport', {
            'fields': ('travel_time', 'distance')
        }),
        ('Notes', {
            'fields': ('client_notes', 'agent_notes', 'system_notes')
        }),
        ('Confirmation', {
            'fields': ('confirmed_at', 'confirmed_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(CalendarConflict)
class CalendarConflictAdmin(admin.ModelAdmin):
    """Admin for CalendarConflict model."""
    list_display = ['schedule1', 'schedule2', 'conflict_type', 'severity', 'status', 'created_at']
    list_filter = ['conflict_type', 'severity', 'status']
    search_fields = ['description']
    readonly_fields = ['id', 'resolved_at', 'created_at', 'updated_at']


@admin.register(SchedulingPreference)
class SchedulingPreferenceAdmin(admin.ModelAdmin):
    """Admin for SchedulingPreference model."""
    list_display = ['user', 'route_optimization', 'client_preference_handling', 'max_daily_visits', 'is_active']
    list_filter = ['route_optimization', 'client_preference_handling', 'is_active']
    search_fields = ['user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ScheduleMetrics)
class ScheduleMetricsAdmin(admin.ModelAdmin):
    """Admin for ScheduleMetrics model."""
    list_display = ['agent', 'date', 'total_scheduled_visits', 'completed_visits', 'cancelled_visits', 'efficiency_score']
    list_filter = ['date']
    search_fields = ['agent__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
