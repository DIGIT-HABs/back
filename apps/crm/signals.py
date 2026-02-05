"""
Signals for CRM management.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import ClientProfile, PropertyInterest, ClientInteraction, Lead


@receiver(post_save, sender=ClientProfile)
def client_profile_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after client profile is created or updated.
    """
    if created:
        # Log profile creation
        from apps.core.models import ActivityLog
        
        ActivityLog.objects.create(
            user=instance.user,
            component='clients',
            action='CLIENT_PROFILE_CREATED',
            message=f'Client profile created for {instance.user.get_full_name()}',
            metadata={
                'content_type': 'ClientProfile',
                'object_id': str(instance.id),
                'changes': {'created': True}
            }
        )
        
        # Send welcome notification
        from apps.core.models import Notification
        
        Notification.objects.create(
            recipient_type='user',
            recipient_id=str(instance.user.id),
            channel='in_app',
            priority='normal',
            title='Bienvenue dans DIGIT-HAB CRM',
            message='Votre profil client a été créé avec succès. Découvrez nos propriétés qui vous correspondent !',
            metadata={'type': 'WELCOME_CLIENT'}
        )
    
    else:
        # Handle profile updates
        from apps.core.models import ActivityLog
        
        # Get old instance to track changes
        try:
            old_instance = ClientProfile.objects.get(id=instance.id)
        except ClientProfile.DoesNotExist:
            return
        
        # Track significant changes
        tracked_fields = ['status', 'priority_level', 'max_budget', 'financing_status']
        changes = {}
        
        for field in tracked_fields:
            if hasattr(old_instance, field) and hasattr(instance, field):
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    changes[field] = {'old': str(old_value), 'new': str(new_value)}
        
        if changes:
            ActivityLog.objects.create(
                user=instance.user,
                component='clients',
                action='CLIENT_PROFILE_UPDATED',
                message=f'Client profile updated for {instance.user.get_full_name()}',
                metadata={
                    'content_type': 'ClientProfile',
                    'object_id': str(instance.id),
                    'changes': changes
                }
            )
            
            # Send notification for important changes
            if 'status' in changes and changes['status']['new'] == 'client':
                Notification.objects.create(
                    recipient_type='user',
                    recipient_id=str(instance.user.id),
                    channel='in_app',
                    priority='normal',
                    title='Statut client activé',
                    message='Félicitations ! Votre statut a été mis à jour en tant que client.',
                    metadata={'type': 'CLIENT_STATUS_UPDATED', 'changes': changes}
                )


@receiver(post_save, sender=PropertyInterest)
def property_interest_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after property interest is created or updated.
    """
    if created:
        from apps.core.models import ActivityLog, Notification
        from apps.properties.models import Property
        
        # Log interest creation
        ActivityLog.objects.create(
            user=instance.client,
            component='properties',
            action='PROPERTY_INTEREST_CREATED',
            message=f'{instance.client.get_full_name()} showed interest in {instance.property.title}',
            metadata={
                'content_type': 'PropertyInterest',
                'object_id': str(instance.id),
                'property': str(instance.property),
                'interaction_type': instance.interaction_type
            }
        )
        
        # Update client activity
        if hasattr(instance.client, 'client_profile'):
            instance.client.client_profile.last_property_view = timezone.now()
            instance.client.client_profile.save(update_fields=['last_property_view'])
        
        # Send notifications for important interactions
        if instance.interaction_type in ['inquiry', 'visit_request', 'offer_made']:
            # Notify agent
            if instance.property.agent:
                Notification.objects.create(
                    recipient_type='user',
                    recipient_id=str(instance.property.agent.id),
                    channel='in_app',
                    priority='high',
                    title='Nouveau intérêt pour votre propriété',
                    message=f'{instance.client.get_full_name()} s\'intéresse à "{instance.property.title}".',
                    metadata={'type': 'NEW_PROPERTY_INTEREST', 'property_id': str(instance.property.id)}
                )
            
            # Notify client
            Notification.objects.create(
                recipient_type='user',
                recipient_id=str(instance.client.id),
                channel='in_app',
                priority='normal',
                title='Intérêt enregistré',
                message=f'Votre intérêt pour "{instance.property.title}" a été enregistré.',
                metadata={'type': 'INTEREST_RECORDED', 'property_id': str(instance.property.id)}
            )
    
    else:
        # Handle interest updates
        from apps.core.models import ActivityLog
        
        try:
            old_instance = PropertyInterest.objects.get(id=instance.id)
        except PropertyInterest.DoesNotExist:
            return
        
        # Track status changes
        if old_instance.status != instance.status:
            ActivityLog.objects.create(
                user=instance.client,
                component='properties',
                action='PROPERTY_INTEREST_UPDATED',
                message=f'Property interest status changed from {old_instance.status} to {instance.status}',
                metadata={
                    'content_type': 'PropertyInterest',
                    'object_id': str(instance.id),
                    'old_status': old_instance.status,
                    'new_status': instance.status
                }
            )


@receiver(post_save, sender=ClientInteraction)
def client_interaction_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after client interaction is created or updated.
    """
    if created:
        from apps.core.models import ActivityLog, Notification
        
        # Log interaction creation
        ActivityLog.objects.create(
            user=instance.agent,
            component='clients',
            action='CLIENT_INTERACTION_CREATED',
            message=f'Interaction created with {instance.client.get_full_name()}',
            metadata={
                'content_type': 'ClientInteraction',
                'object_id': str(instance.id),
                'client': str(instance.client),
                'interaction_type': instance.interaction_type
            }
        )
        
        # Send reminder notifications
        if instance.scheduled_date and instance.scheduled_date > timezone.now():
            # Schedule reminder 1 hour before (Note: created_at cannot be in future, store in metadata)
            Notification.objects.create(
                recipient_type='user',
                recipient_id=str(instance.agent.id),
                channel='in_app',
                priority='high',
                title='Rappel : Interaction programmée',
                message=f'Rappel : Interaction avec {instance.client.get_full_name()} à {instance.scheduled_date}.',
                metadata={
                    'type': 'INTERACTION_REMINDER',
                    'scheduled_for': str(instance.scheduled_date),
                    'interaction_id': str(instance.id)
                }
            )
        
        # Notify client of scheduled interaction
        if instance.status == 'scheduled':
            Notification.objects.create(
                recipient_type='user',
                recipient_id=str(instance.client.id),
                channel='in_app',
                priority='normal',
                title='Interaction programmée',
                message=f'Votre {instance.get_interaction_type_display()} est programmé(e) pour le {instance.scheduled_date}.',
                metadata={'type': 'INTERACTION_SCHEDULED', 'interaction_id': str(instance.id)}
            )
    
    else:
        # Handle interaction updates
        from apps.core.models import ActivityLog, Notification
        
        try:
            old_instance = ClientInteraction.objects.get(id=instance.id)
        except ClientInteraction.DoesNotExist:
            return
        
        # Track status changes
        if old_instance.status != instance.status:
            ActivityLog.objects.create(
                user=instance.agent,
                component='clients',
                action='CLIENT_INTERACTION_UPDATED',
                message=f'Interaction status changed from {old_instance.status} to {instance.status}',
                metadata={
                    'content_type': 'ClientInteraction',
                    'object_id': str(instance.id),
                    'old_status': old_instance.status,
                    'new_status': instance.status
                }
            )
            
            # Send status change notifications
            if instance.status == 'completed':
                # Send summary to client
                Notification.objects.create(
                    recipient_type='user',
                    recipient_id=str(instance.client.id),
                    channel='in_app',
                    priority='normal',
                    title='Interaction terminée',
                    message=f'Votre {instance.get_interaction_type_display()} a été terminé(e). Merci !',
                    metadata={'type': 'INTERACTION_COMPLETED', 'interaction_id': str(instance.id)}
                )
            
            elif instance.status == 'cancelled':
                # Notify client of cancellation
                Notification.objects.create(
                    recipient_type='user',
                    recipient_id=str(instance.client.id),
                    channel='in_app',
                    priority='normal',
                    title='Interaction annulée',
                    message=f'Votre {instance.get_interaction_type_display()} a été annulé(e).',
                    metadata={'type': 'INTERACTION_CANCELLED', 'interaction_id': str(instance.id)}
                )
        
        # Handle follow-up scheduling
        if old_instance.requires_follow_up != instance.requires_follow_up and instance.requires_follow_up:
            # Schedule follow-up reminder
            if instance.follow_up_date:
                Notification.objects.create(
                    recipient_type='user',
                    recipient_id=str(instance.agent.id),
                    channel='in_app',
                    priority='high',
                    title='Suivi programmé',
                    message=f'N\'oubliez pas le suivi avec {instance.client.get_full_name()} le {instance.follow_up_date}.',
                    metadata={
                        'type': 'FOLLOW_UP_SCHEDULED',
                        'follow_up_date': str(instance.follow_up_date),
                        'interaction_id': str(instance.id)
                    }
                )


@receiver(post_save, sender=Lead)
def lead_post_save(sender, instance, created, **kwargs):
    """
    Handle actions after lead is created or updated.
    """
    if created:
        from apps.core.models import ActivityLog, Notification
        
        # Log lead creation
        ActivityLog.objects.create(
            user=instance.assigned_agent or instance.agency.users.filter(role='admin').first(),
            component='clients',
            action='LEAD_CREATED',
            message=f'New lead created: {instance.full_name()}',
            metadata={
                'content_type': 'Lead',
                'object_id': str(instance.id),
                'name': instance.full_name(),
                'email': instance.email,
                'source': instance.source
            }
        )
        
        # Calculate initial score
        instance.calculate_score()
        instance.save(update_fields=['score'])
        
        # Send notification to admin if no agent assigned
        if not instance.assigned_agent:
            admin_users = instance.agency.users.filter(role='admin')
            for admin_user in admin_users:
                Notification.objects.create(
                    recipient_type='user',
                    recipient_id=str(admin_user.id),
                    channel='in_app',
                    priority='high',
                    title='Nouveau lead non assigné',
                    message=f'Nouveau lead de {instance.full_name()} ({instance.email}) nécessite une attribution.',
                    metadata={'type': 'NEW_LEAD_UNASSIGNED', 'lead_id': str(instance.id)}
                )
    
    else:
        # Handle lead updates
        from apps.core.models import ActivityLog
        
        try:
            old_instance = Lead.objects.get(id=instance.id)
        except Lead.DoesNotExist:
            return
        
        # Track significant changes
        changes = {}
        
        # Status changes
        if old_instance.status != instance.status:
            changes['status'] = {'old': old_instance.status, 'new': instance.status}
        
        # Assignment changes
        if old_instance.assigned_agent != instance.assigned_agent:
            changes['assigned_agent'] = {
                'old': str(old_instance.assigned_agent) if old_instance.assigned_agent else 'None',
                'new': str(instance.assigned_agent) if instance.assigned_agent else 'None'
            }
        
        # Qualification changes
        if old_instance.qualification != instance.qualification:
            changes['qualification'] = {
                'old': old_instance.qualification,
                'new': instance.qualification
            }
        
        if changes:
            ActivityLog.objects.create(
                user=instance.assigned_agent or instance.agency.users.filter(role='admin').first(),
                component='clients',
                action='LEAD_UPDATED',
                message=f'Lead updated: {instance.full_name()}',
                metadata={
                    'content_type': 'Lead',
                    'object_id': str(instance.id),
                    'changes': changes
                }
            )
            
            # Handle conversion
            if old_instance.converted_to_client != instance.converted_to_client and instance.converted_to_client:
                # Log conversion
                ActivityLog.objects.create(
                    user=instance.assigned_agent or instance.agency.users.filter(role='admin').first(),
                    component='clients',
                    action='LEAD_CONVERTED',
                    message=f'Lead converted to client: {instance.full_name()}',
                    metadata={
                        'content_type': 'Lead',
                        'object_id': str(instance.id),
                        'conversion_date': str(instance.conversion_date) if instance.conversion_date else None
                    }
                )


@receiver(post_save, sender='auth.User')
def user_post_save(sender, instance, created, **kwargs):
    """
    Handle actions when User model is saved.
    """
    if created and instance.role == 'client':
        # Auto-create client profile for new client users
        from .models import ClientProfile
        
        if not hasattr(instance, 'client_profile'):
            ClientProfile.objects.create(user=instance)


# Connect signals
def connect_signals():
    """Connect all signals for the CRM app."""
    from django.apps import apps
    
    # These signals are connected automatically when the app is loaded
    pass