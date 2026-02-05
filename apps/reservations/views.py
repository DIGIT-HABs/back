"""
Views for reservations management API.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from apps.auth.models import User
from apps.properties.models import Property
from apps.crm.models import ClientProfile
from .models import Reservation, Payment, ReservationActivity
from .serializers import (
    ReservationSerializer, ReservationCreateSerializer, ReservationUpdateSerializer,
    ReservationStatusUpdateSerializer, PaymentSerializer, PaymentCreateSerializer,
    PaymentStatusUpdateSerializer, ReservationActivitySerializer,
    ReservationStatsSerializer
)
from .permissions import (
    IsReservationOwnerOrAgent, CanManageReservations, CanViewAllReservations,
    CanAccessPaymentData, CanProcessPayments, IsAgencyMember,
    CanScheduleVisits, CanModifyReservationStatus, ReadOnly
)
from .services import PaymentService, NotificationService


class ReservationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reservations.
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'reservation_type': ['exact', 'in'],
        'property': ['exact'],
        'client_profile': ['exact'],
        'assigned_agent': ['exact'],
        'scheduled_date': ['gte', 'lte', 'date'],
        'payment_status': ['exact', 'in'],
        'payment_required': ['exact'],
    }
    search_fields = [
        'client_name', 'client_email', 'client_phone', 'client_company',
        'property__title', 'property__address_line1', 'property__city'
    ]
    ordering_fields = [
        'created_at', 'scheduled_date', 'status', 'payment_status',
        'amount', 'property__price'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get reservations based on user permissions."""
        user = self.request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return Reservation.objects.none()
        
        # Staff and superusers see all reservations
        if user.is_staff or user.is_superuser:
            return Reservation.objects.all().select_related(
                'property', 'client_profile__user', 'assigned_agent', 'created_by'
            ).prefetch_related('payments')
        
        # Agents see reservations for their agency
        if user.role in ['agent', 'manager']:
            user_agency = getattr(user.profile, 'agency', None)
            if user_agency:
                return Reservation.objects.filter(
                    property__agency=user_agency
                ).select_related(
                    'property', 'client_profile__user', 'assigned_agent', 'created_by'
                ).prefetch_related('payments')
        
        # Clients see only their own reservations (by profile, email or created_by)
        if user.role == 'client':
            client_profile = getattr(user, 'client_profile', None)
            base = Reservation.objects.select_related(
                'property', 'client_profile__user', 'assigned_agent', 'created_by'
            ).prefetch_related('payments')
            if client_profile:
                return base.filter(
                    Q(client_profile=client_profile)
                    | Q(client_email=user.email)
                    | Q(created_by=user)
                )
            return base.filter(Q(client_email=user.email) | Q(created_by=user))
        
        return Reservation.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return ReservationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ReservationUpdateSerializer
        elif self.action == 'status_update':
            return ReservationStatusUpdateSerializer
        return ReservationSerializer
    
    def get_permissions(self):
        """Get permissions for different actions."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [CanViewAllReservations | ReadOnly]
        elif self.action in ['create', 'my_reservations', 'activities']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsReservationOwnerOrAgent | CanManageReservations]
        elif self.action in ['confirm', 'cancel', 'complete']:
            permission_classes = [IsReservationOwnerOrAgent | CanModifyReservationStatus]
        else:
            permission_classes = [CanManageReservations]
        
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Create reservation and log activity."""
        with transaction.atomic():
            reservation = serializer.save()
            
            # Log activity
            ReservationActivity.objects.create(
                reservation=reservation,
                activity_type='created',
                description=f"Réservation créée par {self.request.user.get_full_name()}",
                performed_by=self.request.user
            )
            
            # Send notification if it's a visit reservation
            if reservation.reservation_type == 'visit':
                NotificationService.send_visit_confirmation(reservation)
    
    def perform_update(self, serializer):
        """Update reservation and log activity."""
        old_instance = self.get_object()
        with transaction.atomic():
            reservation = serializer.save()
            
            # Log activity for significant changes
            if old_instance.status != reservation.status:
                ReservationActivity.objects.create(
                    reservation=reservation,
                    activity_type='status_changed',
                    description=f"Statut modifié de '{old_instance.get_status_display()}' vers '{reservation.get_status_display()}'",
                    old_value=old_instance.status,
                    new_value=reservation.status,
                    performed_by=self.request.user
                )
            else:
                ReservationActivity.objects.create(
                    reservation=reservation,
                    activity_type='updated',
                    description="Réservation modifiée",
                    performed_by=self.request.user
                )
    
    @action(detail=True, methods=['post'], permission_classes=[IsReservationOwnerOrAgent])
    def confirm(self, request, pk=None):
        """Confirm a reservation."""
        reservation = self.get_object()
        
        # Check if user can confirm
        if not reservation.can_be_confirmed_by(request.user):
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à confirmer cette réservation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        with transaction.atomic():
            reservation.confirm(user=request.user)
            
            # Log activity
            ReservationActivity.objects.create(
                reservation=reservation,
                activity_type='confirmed',
                description=f"Réservation confirmée par {request.user.get_full_name()}",
                performed_by=request.user
            )
            
            # Update property status if it's a purchase
            if reservation.reservation_type == 'purchase':
                reservation.property.status = 'reserved'
                reservation.property.save()
            
            # Send confirmation notification
            NotificationService.send_confirmation_notification(reservation)
        
        serializer = self.get_serializer(reservation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsReservationOwnerOrAgent])
    def cancel(self, request, pk=None):
        """Cancel a reservation."""
        reservation = self.get_object()
        reason = request.data.get('reason', '')
        
        # Check if user can cancel
        if not reservation.can_be_cancelled_by(request.user):
            return Response(
                {'error': 'Vous n\'êtes pas autorisé à annuler cette réservation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        with transaction.atomic():
            reservation.cancel(reason=reason, user=request.user)
            
            # Log activity
            ReservationActivity.objects.create(
                reservation=reservation,
                activity_type='cancelled',
                description=f"Réservation annulée par {request.user.get_full_name()}" + 
                           (f". Raison: {reason}" if reason else ""),
                performed_by=request.user
            )
            
            # Update property status back to available
            if reservation.property.status == 'reserved':
                reservation.property.status = 'available'
                reservation.property.save()
            
            # Send cancellation notification
            NotificationService.send_cancellation_notification(reservation, reason)
        
        serializer = self.get_serializer(reservation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsReservationOwnerOrAgent])
    def complete(self, request, pk=None):
        """Mark reservation as completed."""
        reservation = self.get_object()
        notes = request.data.get('notes', '')
        
        with transaction.atomic():
            reservation.complete(notes=notes)
            
            # Log activity
            ReservationActivity.objects.create(
                reservation=reservation,
                activity_type='completed',
                description=f"Réservation marquée comme terminée par {request.user.get_full_name()}",
                performed_by=request.user
            )
        
        serializer = self.get_serializer(reservation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def activities(self, request, pk=None):
        """Get reservation activity log. Access follows get_queryset() (owner/agent/client_email/created_by)."""
        reservation = self.get_object()
        activities = reservation.activities.select_related('performed_by').order_by('-created_at')
        serializer = ReservationActivitySerializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[CanManageReservations])
    def stats(self, request):
        """Get reservation statistics."""
        queryset = self.get_queryset()
        
        # Calculate statistics
        total_reservations = queryset.count()
        pending_reservations = queryset.filter(status='pending').count()
        confirmed_reservations = queryset.filter(status='confirmed').count()
        completed_reservations = queryset.filter(status='completed').count()
        cancelled_reservations = queryset.filter(status='cancelled').count()
        
        total_revenue = queryset.filter(
            status__in=['completed', 'confirmed'],
            amount__isnull=False
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        avg_booking_value = (
            queryset.filter(
                status__in=['completed', 'confirmed'],
                amount__isnull=False
            ).aggregate(
                avg=models.Avg('amount')
            )['avg'] or 0
        )
        
        conversion_rate = (
            (completed_reservations / total_reservations * 100) 
            if total_reservations > 0 else 0
        )
        
        stats = {
            'total_reservations': total_reservations,
            'pending_reservations': pending_reservations,
            'confirmed_reservations': confirmed_reservations,
            'completed_reservations': completed_reservations,
            'cancelled_reservations': cancelled_reservations,
            'total_revenue': total_revenue,
            'avg_booking_value': avg_booking_value,
            'conversion_rate': round(conversion_rate, 2)
        }
        
        serializer = ReservationStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-reservations', permission_classes=[IsAuthenticated])
    def my_reservations(self, request):
        """Get current user's reservations."""
        user = request.user
        
        # Check if user is authenticated (should be guaranteed by permission_classes)
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if user.role == 'client':
            client_profile = getattr(user, 'client_profile', None)
            base = Reservation.objects.select_related(
                'property', 'client_profile__user', 'assigned_agent', 'created_by'
            ).prefetch_related('payments')
            if client_profile:
                queryset = base.filter(
                    Q(client_profile=client_profile)
                    | Q(client_email=user.email)
                    | Q(created_by=user)
                )
            else:
                queryset = base.filter(
                    Q(client_email=user.email) | Q(created_by=user)
                )
        else:
            queryset = Reservation.objects.filter(
                assigned_agent=user
            ).select_related(
                'property', 'client_profile__user', 'assigned_agent', 'created_by'
            ).prefetch_related('payments')
        
        # Apply filters
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payments.
    """
    
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, CanAccessPaymentData]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'reservation': ['exact'],
        'status': ['exact', 'in'],
        'payment_method': ['exact', 'in'],
        'created_at': ['gte', 'lte', 'date'],
    }
    search_fields = ['reservation__client_name', 'reservation__client_email', 'description']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get payments based on user permissions."""
        user = self.request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return Payment.objects.none()
        
        # Staff and superusers see all payments
        if user.is_staff or user.is_superuser:
            return Payment.objects.all().select_related('reservation__property', 'reservation__client_profile__user')
        
        # Agents see payments for their agency's reservations
        if user.role in ['agent', 'manager']:
            user_agency = getattr(user.profile, 'agency', None)
            if user_agency:
                return Payment.objects.filter(
                    reservation__property__agency=user_agency
                ).select_related('reservation__property', 'reservation__client_profile__user')
        
        # Clients see only their own payments
        if user.role == 'client':
            client_profile = getattr(user, 'client_profile', None)
            if client_profile:
                return Payment.objects.filter(
                    reservation__client_profile=client_profile
                ).select_related('reservation__property', 'reservation__client_profile__user')
            else:
                # Fallback to email matching
                return Payment.objects.filter(
                    reservation__client_email=user.email
                ).select_related('reservation__property', 'reservation__client_profile__user')
        
        return Payment.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return PaymentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PaymentStatusUpdateSerializer
        return PaymentSerializer
    
    def get_permissions(self):
        """Get permissions for different actions."""
        if self.action == 'create':
            permission_classes = [CanProcessPayments]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [CanProcessPayments]
        else:
            permission_classes = [CanAccessPaymentData]
        
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Create payment and process it through Stripe."""
        with transaction.atomic():
            payment = serializer.save()
            
            # Process payment through Stripe
            payment_service = PaymentService()
            try:
                payment_intent = payment_service.create_payment_intent(
                    amount=int(payment.amount * 100),  # Convert to cents
                    currency=payment.currency.lower(),
                    reservation_id=str(payment.reservation.id),
                    description=payment.description or f"Paiement pour {payment.reservation}",
                    billing_info={
                        'name': payment.billing_name,
                        'email': payment.billing_email,
                        'phone': payment.billing_phone,
                        'address': {
                            'line1': payment.billing_address_line1,
                            'line2': payment.billing_address_line2,
                            'city': payment.billing_city,
                            'postal_code': payment.billing_postal_code,
                            'country': payment.billing_country or 'FR'
                        }
                    }
                )
                
                payment.stripe_payment_intent_id = payment_intent.id
                payment.save()
                
            except Exception as e:
                payment.mark_as_failed(error_message=str(e))
                raise serializers.ValidationError(f"Erreur lors du traitement du paiement: {str(e)}")
            
            # Log activity
            ReservationActivity.objects.create(
                reservation=payment.reservation,
                activity_type='payment_created',
                description=f"Paiement de {payment.amount} {payment.currency} créé",
                performed_by=self.request.user
            )
    
    @action(detail=True, methods=['post'], permission_classes=[CanProcessPayments])
    def process(self, request, pk=None):
        """Process a payment through Stripe."""
        payment = self.get_object()
        
        if payment.status != 'pending':
            return Response(
                {'error': 'Seuls les paiements en attente peuvent être traités.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_service = PaymentService()
        try:
            result = payment_service.confirm_payment_intent(payment.stripe_payment_intent_id)
            
            if result['status'] == 'succeeded':
                payment.mark_as_completed(charge_id=result.get('charges', [{}])[0].get('id'))
                return Response({'message': 'Paiement traité avec succès.'})
            else:
                payment.mark_as_failed(
                    error_code=result.get('last_payment_error', {}).get('code'),
                    error_message=result.get('last_payment_error', {}).get('message')
                )
                return Response(
                    {'error': f"Paiement échoué: {result.get('last_payment_error', {}).get('message')}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            payment.mark_as_failed(error_message=str(e))
            return Response(
                {'error': f"Erreur lors du traitement: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[CanProcessPayments])
    def refund(self, request, pk=None):
        """Process a refund."""
        payment = self.get_object()
        amount = request.data.get('amount')
        reason = request.data.get('reason', '')
        
        if not payment.can_be_refunded():
            return Response(
                {'error': 'Ce paiement ne peut pas être remboursé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not amount or amount > payment.get_refundable_amount():
            return Response(
                {'error': f'Montant invalide. Maximum remboursable: {payment.get_refundable_amount()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_service = PaymentService()
        try:
            refund = payment_service.create_refund(
                payment.stripe_charge_id,
                amount=int(amount * 100),  # Convert to cents
                reason=reason
            )
            
            if payment.refund(amount, reason):
                # Log activity
                ReservationActivity.objects.create(
                    reservation=payment.reservation,
                    activity_type='refund_created',
                    description=f"Remboursement de {amount} {payment.currency} traité",
                    performed_by=request.user
                )
                
                return Response({'message': 'Remboursement traité avec succès.'})
            else:
                return Response(
                    {'error': 'Erreur lors du traitement du remboursement.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {'error': f"Erreur lors du remboursement: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )