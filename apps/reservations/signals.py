"""
Signals for reservations management.
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from apps.auth.models import User
from apps.properties.models import Property
from apps.crm.models import ClientProfile
from .models import Reservation, Payment, ReservationActivity
from .services import NotificationService, AvailabilityService


@receiver(post_save, sender=Reservation)
def reservation_created_or_updated(sender, instance, created, **kwargs):
    """
    Handle reservation creation and updates.
    """
    if created:
        # Log creation activity
        ReservationActivity.objects.create(
            reservation=instance,
            activity_type='created',
            description=f"Réservation créée",
            performed_by=instance.created_by
        )
        
        # Auto-assign agent if not assigned and property has one
        if not instance.assigned_agent and instance.property.agent:
            instance.assigned_agent = instance.property.agent
            instance.save(update_fields=['assigned_agent'])
        
        # Send confirmation email for visit reservations
        if instance.reservation_type == 'visit':
            NotificationService.send_visit_confirmation(instance)
            
    else:
        # Check for status changes
        try:
            old_instance = Reservation.objects.get(pk=instance.pk)
            
            # Status change
            if old_instance.status != instance.status:
                ReservationActivity.objects.create(
                    reservation=instance,
                    activity_type='status_changed',
                    description=f"Statut modifié de '{old_instance.get_status_display()}' vers '{instance.get_status_display()}'",
                    old_value=old_instance.status,
                    new_value=instance.status,
                    performed_by=instance.updated_at  # Use updated_at as proxy for who made the change
                )
                
                # Handle specific status changes
                if instance.status == 'confirmed' and not old_instance.confirmed_at:
                    NotificationService.send_confirmation_notification(instance)
                    instance.confirmed_at = timezone.now()
                    instance.save(update_fields=['confirmed_at'])
                
                elif instance.status == 'cancelled' and not old_instance.cancelled_at:
                    NotificationService.send_cancellation_notification(instance, instance.cancellation_reason)
                    instance.cancelled_at = timezone.now()
                    instance.save(update_fields=['cancelled_at'])
                
                elif instance.status == 'completed' and not old_instance.completed_at:
                    instance.completed_at = timezone.now()
                    instance.save(update_fields=['completed_at'])
            
            # Agent assignment change
            if old_instance.assigned_agent != instance.assigned_agent and instance.assigned_agent:
                ReservationActivity.objects.create(
                    reservation=instance,
                    activity_type='agent_assigned',
                    description=f"Agent {instance.assigned_agent.get_full_name()} assigné",
                    performed_by=instance.updated_at
                )
            
            # Follow-up date change
            if old_instance.follow_up_date != instance.follow_up_date and instance.follow_up_date:
                ReservationActivity.objects.create(
                    reservation=instance,
                    activity_type='follow_up_scheduled',
                    description=f"Suivi programmé pour le {instance.follow_up_date.strftime('%d/%m/%Y à %H:%M')}",
                    performed_by=instance.updated_at
                )
                
        except Reservation.DoesNotExist:
            pass  # New instance, no old data


@receiver(post_save, sender=Payment)
def payment_created_or_updated(sender, instance, created, **kwargs):
    """
    Handle payment creation and updates.
    """
    if created:
        # Log payment creation
        ReservationActivity.objects.create(
            reservation=instance.reservation,
            activity_type='payment_created',
            description=f"Paiement de {instance.amount} {instance.currency} créé",
        )
        
        # Update reservation payment status
        instance.reservation.payment_status = 'processing'
        instance.reservation.save(update_fields=['payment_status'])
        
    else:
        # Check for status changes
        try:
            old_instance = Payment.objects.get(pk=instance.pk)
            
            # Status change to completed
            if old_instance.status != instance.status and instance.status == 'completed':
                ReservationActivity.objects.create(
                    reservation=instance.reservation,
                    activity_type='payment_completed',
                    description=f"Paiement de {instance.amount} {instance.currency} complété",
                )
                
                # Update reservation payment status
                instance.reservation.payment_status = 'paid'
                instance.reservation.save(update_fields=['payment_status'])
                
                # Send payment confirmation
                NotificationService.send_payment_confirmation(instance)
            
            # Status change to failed
            elif old_instance.status != instance.status and instance.status == 'failed':
                ReservationActivity.objects.create(
                    reservation=instance.reservation,
                    activity_type='payment_failed',
                    description=f"Paiement de {instance.amount} {instance.currency} échoué - {instance.error_message}",
                )
                
                # Update reservation payment status
                instance.reservation.payment_status = 'failed'
                instance.reservation.save(update_fields=['payment_status'])
                
                # Send payment failure notification
                NotificationService.send_payment_failure_notification(instance)
            
            # Refund processing
            elif instance.refunded_amount > old_instance.refunded_amount:
                ReservationActivity.objects.create(
                    reservation=instance.reservation,
                    activity_type='refund_created',
                    description=f"Remboursement de {instance.refunded_amount} {instance.currency} traité",
                )
                
        except Payment.DoesNotExist:
            pass  # New instance, no old data


@receiver(pre_save, sender=Reservation)
def reservation_pre_save(sender, instance, **kwargs):
    """
    Handle reservation pre-save operations.
    """
    # Auto-generate end time if only start time is provided
    if instance.scheduled_date and not instance.scheduled_end_date:
        instance.scheduled_end_date = instance.scheduled_date + timezone.timedelta(minutes=instance.duration_minutes)
    
    # Set expiry time for pending reservations (24 hours from now)
    if instance.status == 'pending' and not instance.expires_at:
        instance.expires_at = timezone.now() + timezone.timedelta(hours=24)
    
    # Update property status based on reservation status
    if instance.pk:  # Existing instance
        try:
            old_instance = Reservation.objects.get(pk=instance.pk)
            
            # Property status changes based on reservation
            if (old_instance.status in ['pending', 'cancelled', 'completed'] and 
                instance.status == 'confirmed' and 
                instance.reservation_type in ['purchase', 'viewing']):
                
                if instance.property.status == 'available':
                    instance.property.status = 'under_offer'
                    instance.property.save(update_fields=['status'])
            
            elif (old_instance.status == 'confirmed' and 
                  instance.status in ['cancelled', 'completed']):
                
                if instance.property.status == 'under_offer':
                    if instance.status == 'completed':
                        instance.property.status = 'sold' if instance.reservation_type == 'purchase' else 'rented'
                    else:  # cancelled
                        instance.property.status = 'available'
                    instance.property.save(update_fields=['status'])
                    
        except Reservation.DoesNotExist:
            pass  # New instance
    
    # Validate availability before confirmation
    elif instance.status == 'confirmed':
        availability = AvailabilityService.check_availability(
            instance.property.id,
            instance.scheduled_date,
            instance.scheduled_end_date,
            instance.duration_minutes
        )
        
        if not availability['available']:
            raise ValueError(f"Propriété non disponible: {availability['reason']}")


@receiver(post_delete, sender=Reservation)
def reservation_deleted(sender, instance, **kwargs):
    """
    Handle reservation deletion.
    """
    # Log deletion activity
    ReservationActivity.objects.create(
        reservation=instance,
        activity_type='cancelled',  # Use cancelled type for consistency
        description=f"Réservation supprimée",
    )
    
    # Restore property status if needed
    if instance.property.status in ['under_offer', 'reserved']:
        instance.property.status = 'available'
        instance.property.save(update_fields=['status'])


@receiver(post_save, sender=ClientProfile)
def client_profile_created(sender, instance, created, **kwargs):
    """
    Handle client profile creation - auto-create related reservations with email.
    """
    if created and instance.user:
        # Check for existing reservations with matching email
        pending_reservations = Reservation.objects.filter(
            client_email=instance.user.email,
            status='pending',
            client_profile__isnull=True
        )
        
        if pending_reservations.exists():
            # Link these reservations to the new client profile
            updated_count = pending_reservations.update(client_profile=instance)
            
            if updated_count > 0:
                # Log the update
                ReservationActivity.objects.create(
                    reservation=pending_reservations.first(),
                    activity_type='updated',
                    description=f"Lien automatique avec profil client créé ({updated_count} réservation(s))",
                )


@receiver(post_save, sender=Property)
def property_updated(sender, instance, **kwargs):
    """
    Handle property updates that might affect existing reservations.
    """
    try:
        # Check if property status changed
        old_property = Property.objects.get(pk=instance.pk)
        
        if old_property.status != instance.status:
            # If property is no longer available, cancel pending reservations
            if instance.status not in ['available', 'under_offer']:
                pending_reservations = Reservation.objects.filter(
                    property=instance,
                    status__in=['pending', 'confirmed']
                )
                
                for reservation in pending_reservations:
                    if reservation.status == 'pending':
                        reservation.cancel(
                            reason=f"Propriété non disponible (statut: {instance.get_status_display()})"
                        )
                    elif reservation.status == 'confirmed':
                        # For confirmed reservations, add internal note
                        reservation.internal_notes += f"\n[{timezone.now()}] ATTENTION: Propriété no longer disponible (statut: {instance.get_status_display()})"
                        reservation.save(update_fields=['internal_notes'])
                        
    except Property.DoesNotExist:
        pass  # New property


def cleanup_expired_reservations():
    """
    Utility function to clean up expired reservations.
    Call this periodically (e.g., via Celery task).
    """
    from django.db import transaction
    
    # Find expired reservations
    expired_reservations = Reservation.objects.filter(
        status='pending',
        expires_at__lt=timezone.now()
    )
    
    with transaction.atomic():
        for reservation in expired_reservations:
            # Mark as expired
            reservation.status = 'expired'
            reservation.save(update_fields=['status'])
            
            # Log activity
            ReservationActivity.objects.create(
                reservation=reservation,
                activity_type='cancelled',
                description="Réservation expirée automatiquement",
            )
            
            # Restore property status
            if reservation.property.status == 'under_offer':
                reservation.property.status = 'available'
                reservation.property.save(update_fields=['status'])


def send_visit_reminders():
    """
    Utility function to send visit reminders.
    Call this periodically (e.g., via Celery task).
    """
    # Find reservations for tomorrow that need reminders
    tomorrow = timezone.now().date() + timezone.timedelta(days=1)
    
    reservations_to_remind = Reservation.objects.filter(
        reservation_type='visit',
        status='confirmed',
        scheduled_date__date=tomorrow,
        # Check if reminder hasn't been sent yet (you might want to add a field for this)
    )
    
    for reservation in reservations_to_remind:
        NotificationService.send_reminder_notification(reservation)


# Connect signals
def connect_signals():
    """
    Connect all signals for the reservations app.
    This should be called in the app's ready() method.
    """
    pass  # Signals are already connected via the @receiver decorators above