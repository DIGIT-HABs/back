"""
Signals for property management.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
# from django.contrib.gis.geos import Point
from .models import Property


@receiver(pre_save, sender=Property)
def property_pre_save(sender, instance, **kwargs):
    """
    Update location field from latitude/longitude before saving.
    """
    # if instance.latitude is not None and instance.longitude is not None:
    #     # Create Point from lat/lon
    #     instance.location = Point(instance.longitude, instance.latitude, srid=4326)


@receiver(post_save, sender=Property)
def property_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after property is saved.
    """
    # Temporarily disabled to allow data creation
    return
    
    if created:
        # Log property creation
        try:
            from apps.core.models import ActivityLog
            from django.contrib.contenttypes.models import ContentType
            
            if instance.agent:
                ActivityLog.objects.create(
                    user=instance.agent,
                    action='PROPERTY_CREATED',
                    content_type=ContentType.objects.get_for_model(instance),
                    object_id=str(instance.id),
                    changes={'created': True}
                )
        except Exception:
            # Silently fail if ActivityLog creation fails
            pass
        
        # Send notification to admin (if needed)
        # Notification.objects.create(...) 
        
        # Update agency statistics (if implemented)
        # update_agency_property_count(instance.agency)
        
    else:
        # Log property updates
        from apps.core.models import ActivityLog
        from django.contrib.contenttypes.models import ContentType
        from django.db.models import Model
        
        # Get the old instance to track changes
        try:
            old_instance = Property.objects.get(id=instance.id)
        except Property.DoesNotExist:
            return
        
        # Track significant field changes
        tracked_fields = ['status', 'price', 'title', 'description']
        changes = {}
        
        for field in tracked_fields:
            if hasattr(old_instance, field) and hasattr(instance, field):
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    changes[field] = {'old': str(old_value), 'new': str(new_value)}
        
        if changes:
            ActivityLog.objects.create(
                user=instance.agent,
                action='PROPERTY_UPDATED',
                content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.id,
                changes=changes
            )
            
            # Send status change notifications
            if 'status' in changes:
                from apps.core.models import Notification
                from django.utils import timezone
                
                Notification.objects.create(
                    recipient=instance.agent,
                    type='PROPERTY_STATUS_CHANGED',
                    title='Statut de propriété modifié',
                    message=f'Le statut de "{instance.title}" a été modifié en "{instance.get_status_display()}".',
                    created_at=timezone.now()
                )


@receiver(post_save, sender='properties.PropertyImage')
def property_image_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after property image is saved.
    """
    # Temporarily disabled - ActivityLog fields mismatch
    return
    
    if created:
        from apps.core.models import ActivityLog
        from django.contrib.contenttypes.models import ContentType
        
        ActivityLog.objects.create(
            user=instance.property.agent,
            action='PROPERTY_IMAGE_ADDED',
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            changes={'property': str(instance.property)}
        )


@receiver(post_save, sender='properties.PropertyDocument')
def property_document_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after property document is saved.
    """
    # Temporarily disabled - ActivityLog fields mismatch
    return
    
    if created:
        from apps.core.models import ActivityLog
        from django.contrib.contenttypes.models import ContentType
        
        ActivityLog.objects.create(
            user=instance.property.agent,
            action='PROPERTY_DOCUMENT_ADDED',
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            changes={'property': str(instance.property)}
        )


@receiver(post_save, sender='properties.PropertyVisit')
def property_visit_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after property visit is saved.
    """
    # Temporarily disabled - ActivityLog fields mismatch
    return
    
    if created:
        from apps.core.models import ActivityLog, Notification
        from django.contrib.contenttypes.models import ContentType
        from django.utils import timezone
        
        # Log visit creation
        ActivityLog.objects.create(
            user=instance.client if instance.client else instance.agent,
            action='PROPERTY_VISIT_CREATED',
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            changes={
                'property': str(instance.property),
                'client': str(instance.client) if instance.client else 'N/A',
                'agent': str(instance.agent)
            }
        )
        
        # Send notifications
        # Notify agent about new visit request
        Notification.objects.create(
            recipient=instance.agent,
            type='NEW_VISIT_REQUEST',
            title='Nouvelle demande de visite',
            message=f'Nouvelle demande de visite pour "{instance.property.title}" le {instance.scheduled_date}.',
            created_at=timezone.now()
        )
        
        # Notify client if they created the visit themselves
        if instance.client and instance.client != instance.agent:
            Notification.objects.create(
                recipient=instance.client,
                type='VISIT_SCHEDULED',
                title='Visite programmée',
                message=f'Votre visite pour "{instance.property.title}" a été programmée le {instance.scheduled_date}.',
                created_at=timezone.now()
            )
    
    else:
        # Handle visit updates (status changes, etc.)
        from apps.core.models import ActivityLog, Notification
        from django.contrib.contenttypes.models import ContentType
        from django.utils import timezone
        
        # Get old instance to track changes
        try:
            old_instance = PropertyVisit.objects.get(id=instance.id)
        except PropertyVisit.DoesNotExist:
            return
        
        # Track status changes
        if old_instance.status != instance.status:
            # Log status change
            ActivityLog.objects.create(
                user=instance.agent,
                action='VISIT_STATUS_CHANGED',
                content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.id,
                changes={
                    'old_status': old_instance.status,
                    'new_status': instance.status
                }
            )
            
            # Send notifications for status changes
            notifications = []
            
            if instance.status == 'confirmed':
                # Notify client that visit is confirmed
                if instance.client:
                    notifications.append((
                        instance.client,
                        'VISIT_CONFIRMED',
                        'Visite confirmée',
                        f'Votre visite pour "{instance.property.title}" le {instance.scheduled_date} a été confirmée.'
                    ))
            elif instance.status == 'cancelled':
                # Notify client that visit is cancelled
                if instance.client:
                    notifications.append((
                        instance.client,
                        'VISIT_CANCELLED',
                        'Visite annulée',
                        f'Votre visite pour "{instance.property.title}" le {instance.scheduled_date} a été annulée.'
                    ))
            elif instance.status == 'completed':
                # Notify agent that visit was completed
                notifications.append((
                    instance.agent,
                    'VISIT_COMPLETED',
                    'Visite terminée',
                    f'La visite pour "{instance.property.title}" le {instance.scheduled_date} a été terminée.'
                ))
            
            # Create notifications
            for recipient, notif_type, title, message in notifications:
                Notification.objects.create(
                    recipient=recipient,
                    type=notif_type,
                    title=title,
                    message=message,
                    created_at=timezone.now()
                )


# Connect signals
def connect_signals():
    """Connect all signals for the properties app."""
    from django.apps import apps
    
    # These signals are connected automatically when the app is loaded
    pass