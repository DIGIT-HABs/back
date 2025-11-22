"""
Signaux pour le système de notifications
Automatisation des notifications en temps réel
"""

import logging
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from .models import Notification, NotificationTemplate
from .services import NotificationService

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notification)
def handle_notification_created(sender, instance, created, **kwargs):
    """Gère la création d'une nouvelle notification"""
    
    if created:
        try:
            # Enregistrer l'activité de création
            logger.info(f"Nouvelle notification créée: {instance.id} pour {instance.recipient.username}")
            
            # La notification sera envoyée via le service NotificationService
            # qui est appelé depuis les views ou les tâches asynchrones
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la notification {instance.id}: {e}")


@receiver(post_save, sender=Notification)
def handle_notification_status_change(sender, instance, created, **kwargs):
    """Gère les changements de statut des notifications"""
    
    if not created:
        try:
            # Détecter les changements de statut
            if instance.status == 'read' and not instance.read_at:
                # La notification vient d'être marquée comme lue
                logger.info(f"Notification {instance.id} marquée comme lue")
            
            elif instance.status == 'delivered' and not instance.delivered_at:
                # La notification vient d'être livrée
                logger.info(f"Notification {instance.id} livrée")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du statut de notification {instance.id}: {e}")


# ============================================================================
# SIGNALS POUR LES MODÈLES EXISTANTS
# ============================================================================

@receiver(post_save, sender='reservations.Reservation')
def handle_reservation_status_change(sender, instance, created, **kwargs):
    """Gère les notifications pour les changements de statut des réservations"""
    
    try:
        if created:
            # Nouvelle réservation créée
            NotificationService.create_notification(
                recipient_ids=[str(instance.client.id)],
                title="Nouvelle réservation confirmée",
                message=f"Votre réservation pour {instance.property.title} a été créée avec succès.",
                notification_type='success',
                priority='normal',
                content_type_id=ContentType.objects.get_for_model(instance).id,
                object_id=instance.id,
                channels=['websocket', 'in_app', 'email']
            )
            
            # Notifier l'agent assigné
            if instance.agent:
                NotificationService.create_notification(
                    recipient_ids=[str(instance.agent.id)],
                    title="Nouvelle réservation assignée",
                    message=f"Une nouvelle réservation a été assignée: {instance.property.title}",
                    notification_type='info',
                    priority='normal',
                    content_type_id=ContentType.objects.get_for_model(instance).id,
                    object_id=instance.id,
                    channels=['websocket', 'in_app']
                )
        
        else:
            # Vérifier les changements de statut
            old_instance = sender.objects.get(id=instance.id)
            
            if old_instance.status != instance.status:
                status_messages = {
                    'confirmed': 'Votre réservation a été confirmée',
                    'cancelled': 'Votre réservation a été annulée',
                    'completed': 'Votre réservation a été marquée comme terminée',
                    'expired': 'Votre réservation a expiré'
                }
                
                if instance.status in status_messages:
                    # Notifier le client
                    NotificationService.create_notification(
                        recipient_ids=[str(instance.client.id)],
                        title="Mise à jour de réservation",
                        message=status_messages[instance.status],
                        notification_type='info' if instance.status in ['confirmed', 'completed'] else 'warning',
                        priority='normal',
                        content_type_id=ContentType.objects.get_for_model(instance).id,
                        object_id=instance.id,
                        channels=['websocket', 'in_app', 'email']
                    )
                    
                    # Notifier l'agent
                    if instance.agent:
                        NotificationService.create_notification(
                            recipient_ids=[str(instance.agent.id)],
                            title="Statut de réservation mis à jour",
                            message=f"La réservation {instance.property.title} est maintenant: {instance.get_status_display()}",
                            notification_type='info',
                            priority='normal',
                            content_type_id=ContentType.objects.get_for_model(instance).id,
                            object_id=instance.id,
                            channels=['websocket', 'in_app']
                        )
    
    except Exception as e:
        logger.error(f"Erreur lors de la notification de réservation {instance.id}: {e}")


@receiver(post_save, sender='reservations.Payment')
def handle_payment_status_change(sender, instance, created, **kwargs):
    """Gère les notifications pour les changements de statut des paiements"""
    
    try:
        if created:
            # Nouveau paiement créé
            NotificationService.create_notification(
                recipient_ids=[str(instance.reservation.client.id)],
                title="Paiement en attente",
                message=f"Un paiement de {instance.amount} {instance.currency} est en attente pour votre réservation.",
                notification_type='info',
                priority='normal',
                content_type_id=ContentType.objects.get_for_model(instance).id,
                object_id=instance.id,
                channels=['websocket', 'in_app', 'email']
            )
        
        else:
            # Vérifier les changements de statut
            old_instance = sender.objects.get(id=instance.id)
            
            if old_instance.status != instance.status:
                if instance.status == 'completed':
                    # Paiement complété
                    NotificationService.create_notification(
                        recipient_ids=[str(instance.reservation.client.id)],
                        title="Paiement confirmé",
                        message=f"Votre paiement de {instance.amount} {instance.currency} a été confirmé avec succès.",
                        notification_type='success',
                        priority='normal',
                        content_type_id=ContentType.objects.get_for_model(instance).id,
                        object_id=instance.id,
                        channels=['websocket', 'in_app', 'email']
                    )
                
                elif instance.status == 'failed':
                    # Paiement échoué
                    NotificationService.create_notification(
                        recipient_ids=[str(instance.reservation.client.id)],
                        title="Échec du paiement",
                        message=f"Votre paiement de {instance.amount} {instance.currency} a échoué. Veuillez réessayer.",
                        notification_type='error',
                        priority='high',
                        content_type_id=ContentType.objects.get_for_model(instance).id,
                        object_id=instance.id,
                        channels=['websocket', 'in_app', 'email']
                    )
                
                elif instance.status in ['refunded', 'partially_refunded']:
                    # Paiement remboursé
                    notification_type = 'success' if instance.status == 'refunded' else 'info'
                    NotificationService.create_notification(
                        recipient_ids=[str(instance.reservation.client.id)],
                        title="Remboursement traité",
                        message=f"Un remboursement de {instance.refunded_amount} {instance.currency} a été effectué.",
                        notification_type=notification_type,
                        priority='normal',
                        content_type_id=ContentType.objects.get_for_model(instance).id,
                        object_id=instance.id,
                        channels=['websocket', 'in_app', 'email']
                    )
    
    except Exception as e:
        logger.error(f"Erreur lors de la notification de paiement {instance.id}: {e}")


@receiver(post_save, sender='properties.Property')
def handle_property_status_change(sender, instance, created, **kwargs):
    """Gère les notifications pour les changements de statut des propriétés"""
    
    try:
        if not created:
            # Vérifier les changements importants
            old_instance = sender.objects.get(id=instance.id)
            
            # Changement de statut (disponible, réservé, vendu, etc.)
            if old_instance.status != instance.status:
                # Notifier les agents et administrateurs
                if hasattr(instance, 'agent') and instance.agent:
                    NotificationService.create_notification(
                        recipient_ids=[str(instance.agent.id)],
                        title="Statut de propriété mis à jour",
                        message=f"La propriété {instance.title} est maintenant: {instance.get_status_display()}",
                        notification_type='info',
                        priority='normal',
                        content_type_id=ContentType.objects.get_for_model(instance).id,
                        object_id=instance.id,
                        channels=['websocket', 'in_app']
                    )
                
                # Notifier les clients potentiels (si applicable)
                if instance.status in ['reserved', 'sold']:
                    # Cette logique pourrait être étendue pour notifier
                    # les clients qui ont marqué cette propriété comme favorite
                    pass
    
    except Exception as e:
        logger.error(f"Erreur lors de la notification de propriété {instance.id}: {e}")


@receiver(post_save, sender='crm.ClientProfile')
def handle_client_profile_update(sender, instance, created, **kwargs):
    """Gère les notifications pour les mises à jour de profil client"""
    
    try:
        if not created:
            # Vérifier les changements importants
            old_instance = sender.objects.get(id=instance.id)
            
            # Changement de statut (nouveau client, prospect, etc.)
            if old_instance.status != instance.status:
                # Notifier l'agent assigné
                if instance.assigned_agent:
                    NotificationService.create_notification(
                        recipient_ids=[str(instance.assigned_agent.id)],
                        title="Client mis à jour",
                        message=f"Le statut du client {instance.user.get_full_name() or instance.user.username} a été mis à jour: {instance.get_status_display()}",
                        notification_type='info',
                        priority='normal',
                        content_type_id=ContentType.objects.get_for_model(instance).id,
                        object_id=instance.id,
                        channels=['websocket', 'in_app']
                    )
    
    except Exception as e:
        logger.error(f"Erreur lors de la notification de profil client {instance.id}: {e}")


# ============================================================================
# NOTIFICATIONS SYSTÈME
# ============================================================================

@receiver(post_save, sender=User)
def handle_user_registration(sender, instance, created, **kwargs):
    """Gère les notifications lors de l'inscription d'un nouvel utilisateur"""
    
    try:
        if created:
            # Créer les paramètres de notification par défaut
            from .models import UserNotificationSetting
            UserNotificationSetting.objects.get_or_create(user=instance)
            
            # Notifier les administrateurs
            admin_users = User.objects.filter(is_superuser=True)
            for admin in admin_users:
                NotificationService.create_notification(
                    recipient_ids=[str(admin.id)],
                    title="Nouvel utilisateur inscrit",
                    message=f"Un nouvel utilisateur s'est inscrit: {instance.get_full_name() or instance.username}",
                    notification_type='info',
                    priority='normal',
                    content_type_id=ContentType.objects.get_for_model(instance).id,
                    object_id=instance.id,
                    channels=['websocket', 'in_app']
                )
    
    except Exception as e:
        logger.error(f"Erreur lors de la notification d'inscription utilisateur {instance.id}: {e}")


@receiver(post_save, sender='auth.User')
def handle_user_profile_update(sender, instance, created, **kwargs):
    """Gère les notifications pour les mises à jour de profil utilisateur"""
    
    try:
        if not created:
            # Vérifier les changements de rôle ou de permissions
            old_instance = sender.objects.get(id=instance.id)
            
            # Changement de statut utilisateur (actif, inactif, etc.)
            if old_instance.is_active != instance.is_active:
                if not instance.is_active:
                    # Utilisateur désactivé - notifier les admins
                    admin_users = User.objects.filter(is_superuser=True)
                    for admin in admin_users:
                        NotificationService.create_notification(
                            recipient_ids=[str(admin.id)],
                            title="Utilisateur désactivé",
                            message=f"L'utilisateur {instance.get_full_name() or instance.username} a été désactivé.",
                            notification_type='warning',
                            priority='normal',
                            channels=['websocket', 'in_app']
                        )
    
    except Exception as e:
        logger.error(f"Erreur lors de la notification de mise à jour utilisateur {instance.id}: {e}")


# ============================================================================
# TÂCHES DE MAINTENANCE
# ============================================================================

@receiver(post_save, sender=Notification)
def cleanup_old_notifications(sender, instance, **kwargs):
    """Nettoie automatiquement les anciennes notifications lues"""
    
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Supprimer les notifications lues de plus de 30 jours
        cutoff_date = timezone.now() - timedelta(days=30)
        
        deleted_count, _ = Notification.objects.filter(
            status='read',
            read_at__lt=cutoff_date
        ).delete()
        
        if deleted_count > 0:
            logger.info(f"{deleted_count} anciennes notifications supprimées")
    
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des anciennes notifications: {e}")


# ============================================================================
# VALIDATION ET VÉRIFICATIONS
# ============================================================================

@receiver(post_save, sender=Notification)
def validate_notification(sender, instance, created, **kwargs):
    """Valide les notifications avant envoi"""
    
    try:
        # Vérifier que la notification a au moins un destinataire
        if not instance.recipient:
            logger.error(f"Notification {instance.id} sans destinataire")
            return
        
        # Vérifier que le message n'est pas vide
        if not instance.message.strip():
            logger.error(f"Notification {instance.id} avec message vide")
            return
        
        # Vérifier la cohérence du statut
        if instance.status == 'sent' and not instance.sent_at:
            instance.sent_at = timezone.now()
            instance.save()
        
        if instance.status == 'delivered' and not instance.delivered_at:
            instance.delivered_at = timezone.now()
            instance.save()
    
    except Exception as e:
        logger.error(f"Erreur lors de la validation de la notification {instance.id}: {e}")