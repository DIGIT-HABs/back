"""
URL configuration for reservations app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'', views.ReservationViewSet, basename='reservation')

app_name = 'reservations'

# Le router génère automatiquement les URLs pour les @action decorators :
# - POST /api/reservations/{id}/confirm/    (via @action confirm)
# - POST /api/reservations/{id}/cancel/     (via @action cancel)
# - POST /api/reservations/{id}/complete/   (via @action complete)
# - GET  /api/reservations/{id}/activities/ (via @action activities)
# - GET  /api/reservations/stats/           (via @action stats)
# - GET  /api/reservations/my-reservations/ (via @action my_reservations)
# - POST /api/reservations/payments/{id}/process/ (via @action process)
# - POST /api/reservations/payments/{id}/refund/  (via @action refund)

urlpatterns = [
    path('', include(router.urls)),
]