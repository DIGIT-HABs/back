"""
Signals for reviews app.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.notifications.services import NotificationService
from .models import Review, ReviewHelpful


@receiver(post_save, sender=Review)
def review_created_or_updated(sender, instance, created, **kwargs):
    """
    Handle review creation and updates.
    Send notifications to relevant parties.
    """
    if created:
        # Notify agent if review is about them or their property
        if instance.agent:
            NotificationService.create_notification(
                recipient_ids=[str(instance.agent.id)],
                notification_type='review_received',
                title='Nouvel avis reçu',
                message=f"{instance.author.get_full_name()} a laissé un avis ({instance.rating}⭐)",
                variables={
                    'review_id': str(instance.id),
                    'review_type': instance.review_type,
                    'rating': instance.rating,
                }
            )
        
        # Notify property agent if different from review agent
        if instance.property and instance.property.agent and instance.property.agent != instance.agent:
            NotificationService.create_notification(
                recipient_ids=[str(instance.property.agent.id)],
                notification_type='review_received',
                title='Nouvel avis sur votre bien',
                message=f"Un avis a été laissé sur {instance.property.title} ({instance.rating}⭐)",
                variables={
                    'review_id': str(instance.id),
                    'property_id': str(instance.property.id),
                    'rating': instance.rating,
                }
            )
    
    # Notify author when review is published
    if instance.is_published and not created:
        # Check if it was just published (would need to track previous state properly)
        NotificationService.create_notification(
            recipient_ids=[str(instance.author.id)],
            notification_type='review_published',
            title='Votre avis a été publié',
            message=f"Votre avis a été vérifié et publié.",
            variables={
                'review_id': str(instance.id),
            }
        )


@receiver(post_save, sender=Review)
def review_response_added(sender, instance, **kwargs):
    """
    Notify author when agent responds to their review.
    """
    if instance.response and instance.response_date:
        NotificationService.create_notification(
            recipient_ids=[str(instance.author.id)],
            notification_type='review_response',
            title='Réponse à votre avis',
            message=f"{instance.response_by.get_full_name() if instance.response_by else 'L\'agent'} a répondu à votre avis.",
            variables={
                'review_id': str(instance.id),
            }
        )


@receiver(post_delete, sender=Review)
def review_deleted(sender, instance, **kwargs):
    """
    Handle review deletion.
    """
    # Clean up helpful votes (should cascade automatically, but just in case)
    ReviewHelpful.objects.filter(review=instance).delete()
