"""
URLs pour le système de calendrier intelligent
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'working-hours', views.WorkingHoursViewSet, basename='workinghours')
router.register(r'time-slots', views.TimeSlotViewSet, basename='timeslot')
router.register(r'client-availabilities', views.ClientAvailabilityViewSet, basename='clientavailability')
router.register(r'schedules', views.VisitScheduleViewSet, basename='visitschedule')
router.register(r'conflicts', views.CalendarConflictViewSet, basename='calendarconflict')
router.register(r'preferences', views.SchedulingPreferenceViewSet, basename='schedulingpreference')
router.register(r'metrics', views.ScheduleMetricsViewSet, basename='schedulemetrics')

urlpatterns = [
    # API REST via router
    path('', include(router.urls)),
    
    # URLs additionnelles
    path('auto-schedule/', views.auto_schedule_view, name='auto_schedule'),
    path('optimize/', views.optimize_schedules_view, name='optimize_schedules'),
    path('generate-slots/', views.generate_time_slots_view, name='generate_time_slots'),
    path('calendar-view/', views.calendar_view, name='calendar_view'),
]