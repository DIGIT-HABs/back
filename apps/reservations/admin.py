"""
Admin configuration for reservations app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Reservation, Payment, ReservationActivity


class PaymentInline(admin.TabularInline):
    """Inline admin for payments."""
    model = Payment
    extra = 0
    fields = ['amount', 'currency', 'status', 'payment_method', 'completed_at']
    readonly_fields = ['id', 'stripe_payment_intent_id', 'completed_at']


class ReservationActivityInline(admin.TabularInline):
    """Inline admin for reservation activities."""
    model = ReservationActivity
    extra = 0
    fields = ['activity_type', 'description', 'performed_by', 'created_at']
    readonly_fields = ['id', 'activity_type', 'description', 'performed_by', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Admin for Reservation model."""
    
    list_display = [
        'id', 'property', 'get_client_display', 'reservation_type', 'status', 
        'scheduled_date', 'payment_status', 'assigned_agent', 'created_at'
    ]
    list_filter = ['reservation_type', 'status', 'payment_status', 'payment_required', 'language_preference', 'scheduled_date', 'created_at']
    search_fields = ['property__title', 'client_profile__user__username', 'client_name', 'client_email', 'client_phone']
    readonly_fields = [
        'id', 'confirmed_at', 'cancelled_at', 'completed_at', 'expires_at',
        'created_at', 'updated_at'
    ]
    inlines = [PaymentInline, ReservationActivityInline]
    
    fieldsets = (
        ('Propriété et client', {
            'fields': ('property', 'client_profile')
        }),
        ('Type et statut', {
            'fields': ('reservation_type', 'status', 'payment_status')
        }),
        ('Tarification', {
            'fields': ('amount', 'currency', 'purchase_price', 'reservation_deposit')
        }),
        ('Dates', {
            'fields': ('scheduled_date', 'scheduled_end_date', 'duration_minutes')
        }),
        ('Informations client (si pas de profil)', {
            'fields': ('client_name', 'client_email', 'client_phone', 'client_company')
        }),
        ('Participants additionnels', {
            'fields': ('additional_participants', 'participant_names')
        }),
        ('Besoins spéciaux', {
            'fields': ('special_requirements', 'language_preference')
        }),
        ('Préférences de contact', {
            'fields': ('preferred_contact_method', 'allow_sms_notifications', 'allow_email_notifications')
        }),
        ('Notes', {
            'fields': ('client_notes', 'internal_notes', 'cancellation_reason', 'completion_notes')
        }),
        ('Attribution agent', {
            'fields': ('assigned_agent',)
        }),
        ('Paiement', {
            'fields': ('payment_required',)
        }),
        ('Transitions de statut', {
            'fields': ('confirmed_at', 'cancelled_at', 'completed_at', 'expires_at')
        }),
        ('Suivi', {
            'fields': ('follow_up_required', 'follow_up_date', 'follow_up_completed')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at', 'created_by')
        }),
    )
    
    def get_client_display(self, obj):
        """Display client name."""
        return obj.get_client_name()
    get_client_display.short_description = "Client"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin for Payment model."""
    
    list_display = [
        'id', 'reservation', 'amount_display', 'payment_method', 
        'status', 'completed_at', 'created_at'
    ]
    list_filter = ['payment_method', 'status', 'currency', 'card_brand', 'created_at']
    search_fields = [
        'reservation__property__title',
        'stripe_payment_intent_id', 'stripe_charge_id', 'stripe_customer_id',
        'billing_email', 'billing_name'
    ]
    readonly_fields = [
        'id', 'stripe_payment_intent_id', 'stripe_charge_id', 'stripe_customer_id',
        'processing_started_at', 'completed_at', 'failed_at', 'cancelled_at', 'refunded_at',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Réservation', {
            'fields': ('reservation',)
        }),
        ('Intégration Stripe', {
            'fields': ('stripe_payment_intent_id', 'stripe_charge_id', 'stripe_customer_id')
        }),
        ('Montant et devise', {
            'fields': ('amount', 'currency')
        }),
        ('Statut et méthode', {
            'fields': ('status', 'payment_method')
        }),
        ('Détails de carte', {
            'fields': ('card_brand', 'card_last_four', 'card_exp_month', 'card_exp_year')
        }),
        ('Adresse de facturation', {
            'fields': ('billing_name', 'billing_email', 'billing_phone', 
                      'billing_address_line1', 'billing_address_line2', 
                      'billing_city', 'billing_postal_code', 'billing_country')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Transitions de statut', {
            'fields': ('processing_started_at', 'completed_at', 'failed_at', 'cancelled_at')
        }),
        ('Informations d\'erreur', {
            'fields': ('error_code', 'error_message', 'failure_reason')
        }),
        ('Remboursement', {
            'fields': ('refunded_amount', 'refund_reason', 'refunded_at')
        }),
        ('Métadonnées', {
            'fields': ('metadata', 'id', 'created_at', 'updated_at')
        }),
    )
    
    def amount_display(self, obj):
        """Display formatted amount."""
        if obj.amount:
            return f"{obj.amount:,.2f} {obj.currency}"
        return "-"
    amount_display.short_description = "Montant"


@admin.register(ReservationActivity)
class ReservationActivityAdmin(admin.ModelAdmin):
    """Admin for ReservationActivity model."""
    
    list_display = ['reservation', 'activity_type', 'performed_by', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['reservation__property__title', 'description']
    readonly_fields = [
        'id', 'reservation', 'activity_type', 'description', 
        'old_value', 'new_value', 'performed_by', 'ip_address', 'user_agent', 'created_at'
    ]
    
    fieldsets = (
        ('Réservation', {
            'fields': ('reservation',)
        }),
        ('Activité', {
            'fields': ('activity_type', 'description')
        }),
        ('Changements', {
            'fields': ('old_value', 'new_value')
        }),
        ('Acteur', {
            'fields': ('performed_by',)
        }),
        ('Contexte', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
