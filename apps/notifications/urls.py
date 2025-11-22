"""
URLs pour le système de notifications
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'templates', views.NotificationTemplateViewSet, basename='notificationtemplate')
router.register(r'settings', views.UserNotificationSettingViewSet, basename='usernotificationsetting')
router.register(r'groups', views.NotificationGroupViewSet, basename='notificationgroup')
router.register(r'logs', views.NotificationLogViewSet, basename='notificationlog')
router.register(r'subscriptions', views.NotificationSubscriptionViewSet, basename='notificationsubscription')

urlpatterns = [
    # API REST via router
    path('', include(router.urls)),
    
    # URLs additionnelles si nécessaire
    # path('test/', views.test_notification_endpoint, name='test_notification'),
]