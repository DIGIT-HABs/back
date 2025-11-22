"""
Signals for core app.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import ActivityLog, Notification, SystemStats, WebhookEvent

User = get_user_model()


@receiver(pre_save, sender=User)
def log_user_changes(sender, instance, **kwargs):
    """Log user changes."""
    # Temporarily disabled to allow data creation
    return
    
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            # Check for important changes
            changes = []
            if old_instance.is_active != instance.is_active:
                changes.append(f"is_active: {old_instance.is_active} -> {instance.is_active}")
            # if old_instance.is_verified != instance.is_verified:
            #     changes.append(f"is_verified: {old_instance.is_verified} -> {instance.is_verified}")
            # if old_instance.last_login != instance.last_login:
            #     changes.append("user logged in")
            
            if changes:
                ActivityLog.objects.create(
                    component='auth',
                    action='user_updated',
                    message=f"User {instance.username} updated: {', '.join(changes)}",
                    user=instance,
                    metadata={'changes': changes}
                )
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=User)
def create_user_activity_log(sender, instance, created, **kwargs):
    """Create activity log for user actions."""
    # Temporarily disabled to allow data creation
    return
    
    if created:
        ActivityLog.objects.create(
            component='auth',
            action='user_created',
            message=f"User {instance.username} created",
            user=instance
        )
    
    # Log login activity
    if hasattr(instance, '_login_activity'):
        ActivityLog.objects.create(
            component='auth',
            action='user_login',
            message=f"User {instance.username} logged in",
            user=instance,
            metadata={'login_count': instance.login_count}
        )


@receiver(post_save, sender=User)
def create_user_notification(sender, instance, created, **kwargs):
    """Create notifications for user events."""
    # Temporarily disabled to allow data creation
    return
    
    if created:
        # Welcome notification for new users
        Notification.objects.create(
            recipient_type='user',
            recipient_id=str(instance.id),
            title='Bienvenue sur DIGIT-HAB CRM',
            message='Votre compte a été créé avec succès. Commencez par compléter votre profil.',
            priority='normal',
            channel='in_app',
            metadata={'user_creation': True}
        )
    
    # Notification for account activation
    if not created and instance.is_active and hasattr(instance, '_activation_change'):
        Notification.objects.create(
            recipient_type='user',
            recipient_id=str(instance.id),
            title='Compte activé',
            message='Votre compte a été activé. Vous pouvez maintenant utiliser toutes les fonctionnalités.',
            priority='high',
            channel='in_app',
            metadata={'account_activation': True}
        )


@receiver(post_save, sender='properties.Property')
def log_property_changes(sender, instance, created, **kwargs):
    """Log property changes."""
    # Temporarily disabled to allow data creation
    return
    
    if created:
        ActivityLog.objects.create(
            component='properties',
            action='property_created',
            message=f"Property '{instance.title}' created by {instance.agent.username if instance.agent else 'System'}",
            user=instance.agent,
            metadata={'property_id': str(instance.id), 'price': str(instance.price)}
        )
    else:
        # Check for important changes
        try:
            old_instance = Property.objects.get(pk=instance.pk)
            changes = []
            
            if old_instance.status != instance.status:
                changes.append(f"status: {old_instance.status} -> {instance.status}")
            if old_instance.price != instance.price:
                changes.append(f"price: {old_instance.price} -> {instance.price}")
            
            if changes:
                ActivityLog.objects.create(
                    component='properties',
                    action='property_updated',
                    message=f"Property '{instance.title}' updated: {', '.join(changes)}",
                    user=instance.agent,
                    metadata={'property_id': str(instance.id), 'changes': changes}
                )
        except Property.DoesNotExist:
            pass


@receiver(post_save, sender='properties.PropertyVisit')
def handle_visit_scheduling(sender, instance, created, **kwargs):
    """Handle visit scheduling notifications."""
    if created and instance.status == 'scheduled':
        # Notify agent about new visit
        if instance.agent:
            Notification.objects.create(
                recipient_type='user',
                recipient_id=str(instance.agent.id),
                title='Nouvelle visite programmée',
                message=f'Visite programmée pour {instance.property.title} le {instance.scheduled_date} à {instance.scheduled_time}',
                priority='high',
                channel='in_app',
                metadata={
                    'visit_id': str(instance.id),
                    'property_id': str(instance.property.id),
                    'visitor_email': instance.visitor_email
                }
            )


@receiver(post_save, sender='properties.PropertyVisit')
def log_visit_changes(sender, instance, created, **kwargs):
    """Log visit changes."""
    if not created:
        try:
            old_instance = PropertyVisit.objects.get(pk=instance.pk)
            
            if old_instance.status != instance.status:
                ActivityLog.objects.create(
                    component='properties',
                    action='visit_status_changed',
                    message=f"Visit status changed: {old_instance.status} -> {instance.status} for {instance.property.title}",
                    user=instance.agent,
                    metadata={
                        'visit_id': str(instance.id),
                        'property_id': str(instance.property.id),
                        'old_status': old_instance.status,
                        'new_status': instance.status
                    }
                )
        except PropertyVisit.DoesNotExist:
            pass


def create_system_stats_periodically():
    """Create periodic system statistics."""
    User = get_user_model()
    
    try:
        # User statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        # verified_users = User.objects.filter(is_verified=True).count()
        
        # Property statistics
        try:
            from apps.properties.models import Property
            total_properties = Property.objects.count()
            available_properties = Property.objects.filter(status='available').count()
        except:
            total_properties = 0
            available_properties = 0
        
        # Create stats records
        stats_data = [
            ('users_count', total_users),
            ('active_users', active_users),
            # ('verified_users', verified_users),
            ('properties_count', total_properties),
            ('available_properties', available_properties),
        ]
        
        for metric, value in stats_data:
            SystemStats.objects.update_or_create(
                metric=metric,
                period='daily',
                defaults={'value': value, 'recorded_at': timezone.now()}
            )
            
    except Exception as e:
        ActivityLog.objects.create(
            component='system',
            action='stats_creation_error',
            message=f"Error creating system stats: {str(e)}",
            level='ERROR'
        )


# Connect signals for property model
try:
    from apps.properties.models import Property, PropertyVisit
    post_save.connect(log_property_changes, sender=Property)
    post_save.connect(handle_visit_scheduling, sender=PropertyVisit)
    post_save.connect(log_visit_changes, sender=PropertyVisit)
except ImportError:
    # Properties app not available yet
    pass