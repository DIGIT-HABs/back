"""
Serializers for reservations management API.
"""

from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.auth.models import User
from apps.properties.models import Property
from apps.crm.models import ClientProfile
from .models import Reservation, Payment, ReservationActivity


class PropertySummarySerializer(serializers.ModelSerializer):
    """Summary serializer for property in reservations."""
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'property_type', 'status', 'price',
            'address_line1', 'city', 'postal_code', 'surface_area',
            'bedrooms', 'bathrooms'
        ]


class ClientSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for client in reservations."""
    
    class Meta:
        model = ClientProfile
        fields = [
            'id', 'user', 'preferred_contact_method',
            'preferred_contact_time', 'max_budget', 'min_budget'
        ]
    
    def to_representation(self, instance):
        """Custom representation with user details."""
        data = super().to_representation(instance)
        if instance.user:
            data['user'] = {
                'id': instance.user.id,
                'username': instance.user.username,
                'first_name': instance.user.first_name,
                'last_name': instance.user.last_name,
                'email': instance.user.email,
                'phone': getattr(instance.user, 'phone', None)
            }
        return data


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payment information."""
    
    class Meta:
        model = Payment
        fields = [
            'id', 'amount', 'currency', 'status', 'payment_method',
            'card_brand', 'card_last_four', 'description',
            'created_at', 'updated_at', 'processing_started_at',
            'completed_at', 'failed_at', 'refunded_amount',
            'refunded_at', 'error_message'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'processing_started_at',
            'completed_at', 'failed_at', 'refunded_at', 'refunded_amount'
        ]


class ReservationActivitySerializer(serializers.ModelSerializer):
    """Serializer for reservation activity log."""
    
    performed_by_name = serializers.CharField(
        source='performed_by.get_full_name',
        read_only=True
    )
    ip_address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    class Meta:
        model = ReservationActivity
        fields = [
            'id', 'activity_type', 'description', 'old_value', 'new_value',
            'performed_by', 'performed_by_name', 'ip_address', 'user_agent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ReservationSerializer(serializers.ModelSerializer):
    """Serializer for reservation management."""
    
    # Nested serializers
    property = PropertySummarySerializer(read_only=True)
    property_id = serializers.UUIDField(write_only=True)
    client_profile = ClientSummarySerializer(read_only=True)
    client_profile_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    assigned_agent_name = serializers.CharField(
        source='assigned_agent.get_full_name',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    
    # Computed fields
    client_name_display = serializers.CharField(source='get_client_name', read_only=True)
    total_participants = serializers.IntegerField(source='get_total_participants', read_only=True)
    outstanding_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        source='get_outstanding_amount',
        read_only=True
    )
    
    # Status information
    is_expired = serializers.BooleanField(read_only=True)
    can_be_cancelled = serializers.SerializerMethodField()
    can_be_confirmed = serializers.SerializerMethodField()
    
    # Payment information
    payments = PaymentSerializer(many=True, read_only=True)
    payment_status_display = serializers.CharField(
        source='get_payment_status_display',
        read_only=True
    )
    
    class Meta:
        model = Reservation
        fields = [
            # Basic Information
            'id', 'reservation_type', 'status', 'amount', 'currency',
            
            # Property and Client
            'property', 'property_id', 'client_profile', 'client_profile_id',
            'client_name', 'client_email', 'client_phone', 'client_company',
            
            # Dates and Duration
            'scheduled_date', 'scheduled_end_date', 'duration_minutes',
            
            # Purchase Information
            'purchase_price', 'reservation_deposit',
            
            # Participants
            'additional_participants', 'participant_names',
            
            # Special Requirements
            'special_requirements', 'language_preference',
            'preferred_contact_method', 'allow_sms_notifications', 'allow_email_notifications',
            
            # Notes
            'client_notes', 'internal_notes', 'cancellation_reason', 'completion_notes',
            
            # Agent Assignment
            'assigned_agent', 'assigned_agent_name',
            
            # Payment
            'payment_required', 'payment_status', 'payment_status_display',
            
            # Status Transitions
            'confirmed_at', 'cancelled_at', 'completed_at', 'expires_at',
            
            # Follow-up
            'follow_up_required', 'follow_up_date', 'follow_up_completed',
            
            # Computed fields
            'client_name_display', 'total_participants', 'outstanding_amount',
            'is_expired', 'can_be_cancelled', 'can_be_confirmed',
            
            # Related data
            'payments',
            
            # Metadata
            'created_at', 'updated_at', 'created_by', 'created_by_name',
        ]
        read_only_fields = [
            'id', 'status', 'confirmed_at', 'cancelled_at', 'completed_at',
            'created_at', 'updated_at', 'payment_status'
        ]
    
    def get_can_be_cancelled(self, obj):
        """Check if reservation can be cancelled."""
        request = self.context.get('request')
        if request and request.user:
            return obj.can_be_cancelled_by(request.user)
        return False
    
    def get_can_be_confirmed(self, obj):
        """Check if reservation can be confirmed."""
        request = self.context.get('request')
        if request and request.user:
            return obj.can_be_confirmed_by(request.user)
        return False
    
    def validate_scheduled_date(self, value):
        """Validate scheduled date."""
        if value and value < timezone.now():
            raise serializers.ValidationError("La date de réservation ne peut pas être dans le passé.")
        return value
    
    def validate_reservation_deposit(self, value):
        """Validate reservation deposit amount."""
        if value and value < 0:
            raise serializers.ValidationError("Le montant de réservation doit être positif.")
        return value
    
    def validate_client_email(self, value):
        """Validate client email if provided."""
        if value and not self.instance and not self.initial_data.get('client_profile_id'):
            # Check if email already exists for another reservation
            existing = Reservation.objects.filter(
                client_email=value,
                status__in=['pending', 'confirmed']
            ).exclude(pk=getattr(self.instance, 'pk', None))
            if existing.exists():
                raise serializers.ValidationError("Cette adresse email a déjà une réservation active.")
        return value
    
    def validate(self, data):
        """Cross-field validation."""
        # Validate scheduled dates
        if data.get('scheduled_date') and data.get('scheduled_end_date'):
            if data['scheduled_end_date'] <= data['scheduled_date']:
                raise serializers.ValidationError({
                    'scheduled_end_date': "La date de fin doit être postérieure à la date de début."
                })
        
        # Validate deposit vs amount
        if data.get('reservation_deposit') and data.get('amount'):
            if data['reservation_deposit'] > data['amount']:
                raise serializers.ValidationError({
                    'reservation_deposit': "Le montant de réservation ne peut pas dépasser le montant total."
                })
        
        # Validate property is available
        if data.get('property_id'):
            try:
                property_obj = Property.objects.get(id=data['property_id'])
                if property_obj.status not in ['available', 'under_offer']:
                    raise serializers.ValidationError({
                        'property_id': f"Le bien n'est pas disponible (statut: {property_obj.get_status_display()})."
                    })
            except Property.DoesNotExist:
                raise serializers.ValidationError({
                    'property_id': "Le bien spécifié n'existe pas."
                })
        
        # Set default values
        if not data.get('assigned_agent') and hasattr(self.context.get('request'), 'user'):
            data['assigned_agent'] = self.context['request'].user
        
        if not data.get('created_by') and hasattr(self.context.get('request'), 'user'):
            data['created_by'] = self.context['request'].user
        
        return data


class ReservationCreateSerializer(ReservationSerializer):
    """Serializer for creating new reservations."""
    
    class Meta(ReservationSerializer.Meta):
        read_only_fields = ReservationSerializer.Meta.read_only_fields + [
            'confirmed_at', 'cancelled_at', 'completed_at', 'payment_status'
        ]


class ReservationUpdateSerializer(ReservationSerializer):
    """Serializer for updating reservations."""
    
    class Meta(ReservationSerializer.Meta):
        read_only_fields = ReservationSerializer.Meta.read_only_fields + [
            'id', 'property', 'property_id', 'client_profile', 'client_profile_id',
            'created_at', 'created_by'
        ]


class ReservationStatusUpdateSerializer(serializers.Serializer):
    """Serializer for status updates."""
    
    status = serializers.ChoiceField(
        choices=['confirmed', 'cancelled', 'completed', 'expired']
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_status(self, value):
        """Validate status change."""
        reservation = self.instance
        
        # Define allowed status transitions
        allowed_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['completed', 'cancelled'],
            'cancelled': [],  # Cancelled reservations cannot be changed
            'completed': [],  # Completed reservations cannot be changed
            'expired': [],    # Expired reservations cannot be changed
        }
        
        current_status = reservation.status
        if value not in allowed_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Transition de statut non autorisée de '{current_status}' vers '{value}'"
            )
        
        return value


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payments."""
    
    reservation = ReservationSerializer(read_only=True)
    reservation_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'reservation', 'reservation_id',
            'amount', 'currency', 'payment_method',
            'description', 'billing_name', 'billing_email', 'billing_phone',
            'billing_address_line1', 'billing_address_line2',
            'billing_city', 'billing_postal_code', 'billing_country'
        ]
    
    def validate_amount(self, value):
        """Validate payment amount."""
        if value <= 0:
            raise serializers.ValidationError("Le montant du paiement doit être positif.")
        return value
    
    def validate(self, data):
        """Cross-field validation."""
        # Validate reservation exists and can be paid
        try:
            reservation = Reservation.objects.get(id=data['reservation_id'])
        except Reservation.DoesNotExist:
            raise serializers.ValidationError({
                'reservation_id': "La réservation spécifiée n'existe pas."
            })
        
        # Check if reservation requires payment
        if not reservation.requires_payment():
            raise serializers.ValidationError({
                'reservation_id': "Cette réservation ne nécessite pas de paiement."
            })
        
        # Check outstanding amount
        outstanding = reservation.get_outstanding_amount()
        if data['amount'] > outstanding:
            raise serializers.ValidationError({
                'amount': f"Le montant ne peut pas dépasser le solde restant ({outstanding} {reservation.currency})."
            })
        
        data['reservation'] = reservation
        return data


class PaymentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for payment status updates."""
    
    status = serializers.ChoiceField(
        choices=[
            'processing', 'completed', 'failed', 'cancelled',
            'refunded', 'partial_refund'
        ]
    )
    error_code = serializers.CharField(required=False, allow_blank=True)
    error_message = serializers.CharField(required=False, allow_blank=True)
    failure_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate status update."""
        payment = self.instance
        
        # Define allowed status transitions
        allowed_transitions = {
            'pending': ['processing', 'failed', 'cancelled'],
            'processing': ['completed', 'failed'],
            'completed': ['refunded', 'partial_refund'],
            'failed': [],  # Failed payments cannot be changed
            'cancelled': [],  # Cancelled payments cannot be changed
            'refunded': [],  # Refunded payments cannot be changed
            'partial_refund': ['refunded'],  # Can complete the refund
        }
        
        current_status = payment.status
        new_status = data['status']
        
        if new_status not in allowed_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Transition de statut non autorisée de '{current_status}' vers '{new_status}'"
            )
        
        return data


class ReservationStatsSerializer(serializers.Serializer):
    """Serializer for reservation statistics."""
    
    total_reservations = serializers.IntegerField()
    pending_reservations = serializers.IntegerField()
    confirmed_reservations = serializers.IntegerField()
    completed_reservations = serializers.IntegerField()
    cancelled_reservations = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_booking_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    conversion_rate = serializers.FloatField()