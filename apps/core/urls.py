"""
URL configuration for core app.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'configurations', views.ConfigurationViewSet, basename='configuration')
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'activity-logs', views.ActivityLogViewSet, basename='activitylog')
router.register(r'file-uploads', views.FileUploadViewSet, basename='fileupload')

urlpatterns = [
    # System health check
    path('health/', views.health_check, name='health_check'),
    
    # System statistics
    path('stats/', views.system_stats, name='system_stats'),
    
    # File upload
    path('upload/', views.FileUploadAPIView.as_view(), name='file_upload'),
    
    # API versioning
    path('version/', views.api_version, name='api_version'),
]

# Include router URLs
urlpatterns += router.urls