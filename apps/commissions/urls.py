"""
URL configuration for commission management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommissionViewSet, PaymentViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'commissions', CommissionViewSet, basename='commission')
router.register(r'payments', PaymentViewSet, basename='payment')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]
