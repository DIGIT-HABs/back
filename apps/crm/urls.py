"""
URL configuration for CRM management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientProfileViewSet, PropertyInterestViewSet, ClientInteractionViewSet,
    LeadViewSet, PropertyMatchingViewSet, DashboardViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'clients', ClientProfileViewSet, basename='clientprofile')
router.register(r'interests', PropertyInterestViewSet, basename='propertyinterest')
router.register(r'interactions', ClientInteractionViewSet, basename='clientinteraction')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'matching', PropertyMatchingViewSet, basename='propertmatching')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]