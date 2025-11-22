"""
URL configuration for property management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, PropertyImageViewSet, PropertyDocumentViewSet, PropertyVisitViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'images', PropertyImageViewSet, basename='propertyimage')
router.register(r'documents', PropertyDocumentViewSet, basename='propertydocument')
router.register(r'visits', PropertyVisitViewSet, basename='propertyvisit')
router.register(r'', PropertyViewSet, basename='property')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]