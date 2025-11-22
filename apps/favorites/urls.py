"""
URL configuration for favorites management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FavoriteViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'', FavoriteViewSet, basename='favorite')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]

