"""
Services pour le système de notifications en temps réel
Intégration avec Django Channels, WebSockets et canaux multiples
"""

import json
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.utils import timezone
from django.template import Template, Context
import asyncio
import channels.layers

from .models import (
    Notification, NotificationTemplate, UserNotificationSetting,
    NotificationGroup, NotificationLog, NotificationSubscription
)

User = get_user_model()
logger = logging.getLogger(__name__)


class WebSocketService:
    """Service pour les notifications WebSocket en temps réel"""
    
    @staticmethod
    async def send_to_user(user_id: str, message: Dict[str, Any]) -> bool:
        """Envoie une notification WebSocket à un utilisateur spécifique"""
        try:
            channel_layer = channels.layers.get_channel_layer()
            if not channel_layer:
                logger.warning("Channel layer non disponible pour WebSocket")
                return False
            
            # Envoyer au groupe personnel de l'utilisateur
            group_name = f"user_{user_id}"
            await channel_layer.group_send(
                group_name,
                {
                    "type": "send_notification",
                    "message": message
                }
            )
            
            # Mettre à jour le last_seen de l'abonnement
            NotificationSubscription.objects.filter(
                user_id=user_id,
                channel_type='user',
                is_active=True
            ).update(last_seen=timezone.now())
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi WebSocket utilisateur {user_id}: {e}")
            return False
    
    @staticmethod
    async def send_to_group(group_id: str, message: Dict[str, Any]) -> bool:
        """Envoie une notification WebSocket à un groupe"""
        try:
            channel_layer = channels.layers.get_channel_layer()
            if not channel_layer:
                return False
            
            group_name = f"group_{group_id}"
            await channel_layer.group_send(
                group_name,
                {
                    "type": "send_notification",
                    "message": message
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi WebSocket groupe {group_id}: {e}")
            return False
    
    @staticmethod
    async def send_to_property(property_id: int, message: Dict[str, Any]) -> bool:
        """Envoie une notification WebSocket liée à une propriété"""
        try:
            channel_layer = channels.layers.get_channel_layer()
            if not channel_layer:
                return False
            
            group_name = f"property_{property_id}"
            await channel_layer.group_send(
                group_name,
                {
                    "type": "send_notification",
                    "message": message
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi WebSocket propriété {property_id}: {e}")
            return False
    
    @staticmethod
    async def send_to_reservation(reservation_id: str, message: Dict[str, Any]) -> bool:
        """Envoie une notification WebSocket liée à une réservation"""
        try:
            channel_layer = channels.layers.get_channel_layer()
            if not channel_layer:
                return False
            
            group_name = f"reservation_{reservation_id}"
            await channel_layer.group_send(
                group_name,
                {
                    "type": "send_notification",
                    "message": message
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi WebSocket réservation {reservation_id}: {e}")
            return False
    
    @staticmethod
    async def broadcast(message: Dict[str, Any], user_ids: List[str] = None) -> Dict[str, bool]:
        """Diffuse un message à plusieurs utilisateurs"""
        results = {}
        
        if user_ids:
            # Envoi ciblé
            for user_id in user_ids:
                results[user_id] = await WebSocketService.send_to_user(user_id, message)
        else:
            # Diffusion générale (pour les administrateurs)
            admin_users = User.objects.filter(
                is_superuser=True
            ).values_list('id', flat=True)
            
            for user_id in admin_users:
                results[str(user_id)] = await WebSocketService.send_to_user(str(user_id), message)
        
        return results


class EmailService:
    """Service pour les notifications par email"""
    
    @staticmethod
    def send_notification_email(notification: Notification) -> bool:
        """Envoie une notification par email"""
        try:
            if not notification.recipient.email:
                logger.warning(f"Utilisateur {notification.recipient.id} n'a pas d'email")
                return False
            
            # Vérifier les préférences utilisateur
            try:
                settings_obj = notification.recipient.notification_settings
                if not settings_obj.email_enabled:
                    logger.info(f"Email désactivé pour utilisateur {notification.recipient.id}")
                    return False
                
                # Vérifier les heures silencieuses
                if settings_obj.is_in_quiet_hours():
                    logger.info(f"Email retardé - heures silencieuses pour {notification.recipient.id}")
                    return False
            except UserNotificationSetting.DoesNotExist:
                # Paramètres par défaut si pas configurés
                pass
            
            # Préparer le contenu
            subject = notification.title
            if notification.template and notification.template.subject:
                subject = notification.template.subject
            
            # Traiter le template avec les variables
            message = notification.message
            if notification.template:
                template = Template(notification.template.message_template)
                context = Context(notification.metadata or {})
                message = template.render(context)
            
            # Envoyer l'email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.recipient.email],
                fail_silently=False
            )
            
            # Marquer comme envoyé
            notification.mark_as_sent('email')
            
            # Log
            NotificationLog.objects.create(
                notification=notification,
                channel='email',
                status='sent',
                sent_at=timezone.now()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email notification {notification.id}: {e}")
            
            # Log d'erreur
            NotificationLog.objects.create(
                notification=notification,
                channel='email',
                status='failed',
                error_message=str(e),
                failed_at=timezone.now()
            )
            
            return False
    
    @staticmethod
    def send_bulk_email(notifications: List[Notification]) -> Dict[str, int]:
        """Envoie des emails en lot"""
        results = {
            'sent': 0,
            'failed': 0,
            'skipped': 0
        }
        
        for notification in notifications:
            if EmailService.send_notification_email(notification):
                results['sent'] += 1
            else:
                results['failed'] += 1
        
        return results


class SMSService:
    """Service pour les notifications SMS (Twilio)"""
    
    @staticmethod
    def send_notification_sms(notification: Notification) -> bool:
        """Envoie une notification SMS"""
        try:
            # Vérifier les préférences
            try:
                settings_obj = notification.recipient.notification_settings
                if not settings_obj.sms_enabled:
                    return False
                
                if settings_obj.is_in_quiet_hours():
                    return False
            except UserNotificationSetting.DoesNotExist:
                return False
            
            # Vérifier que l'utilisateur a un téléphone
            if not hasattr(notification.recipient, 'profile') or not notification.recipient.profile.phone:
                logger.warning(f"Utilisateur {notification.recipient.id} n'a pas de téléphone")
                return False
            
            # Configuration Twilio
            from twilio.rest import Client
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            # Préparer le message (limite SMS)
            message = notification.message[:160]  # Limite SMS standard
            
            # Envoyer le SMS
            message_sid = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=notification.recipient.profile.phone
            )
            
            # Marquer comme envoyé
            notification.mark_as_sent('sms')
            
            # Log
            NotificationLog.objects.create(
                notification=notification,
                channel='sms',
                status='sent',
                external_id=message_sid.sid,
                sent_at=timezone.now()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi SMS notification {notification.id}: {e}")
            
            NotificationLog.objects.create(
                notification=notification,
                channel='sms',
                status='failed',
                error_message=str(e),
                failed_at=timezone.now()
            )
            
            return False


class PushNotificationService:
    """Service pour les notifications push"""
    
    @staticmethod
    def send_notification_push(notification: Notification) -> bool:
        """Envoie une notification push"""
        try:
            # Vérifier les préférences
            try:
                settings_obj = notification.recipient.notification_settings
                if not settings_obj.push_enabled:
                    return False
            except UserNotificationSetting.DoesNotExist:
                return False
            
            # Logique de notification push (Firebase/FCM)
            # Pour l'instant, on simule le comportement
            logger.info(f"Notification push simulée pour {notification.recipient.id}: {notification.title}")
            
            # Marquer comme envoyé
            notification.mark_as_sent('push')
            
            NotificationLog.objects.create(
                notification=notification,
                channel='push',
                status='sent',
                sent_at=timezone.now()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi push notification {notification.id}: {e}")
            return False


class NotificationService:
    """Service principal pour la gestion des notifications"""
    
    @staticmethod
    def create_notification(
        recipient_ids: List[str] = None,
        group_id: str = None,
        template_id: str = None,
        title: str = None,
        message: str = None,
        notification_type: str = 'info',
        priority: str = 'normal',
        content_type_id: int = None,
        object_id: int = None,
        channels: List[str] = None,
        variables: Dict[str, Any] = None
    ) -> List[Notification]:
        """Crée et envoie des notifications"""
        
        notifications_created = []
        
        # Déterminer les destinataires
        recipients = []
        
        if group_id:
            try:
                group = NotificationGroup.objects.get(id=group_id, is_active=True)
                recipients.extend(list(group.users.all()))
            except NotificationGroup.DoesNotExist:
                logger.error(f"Groupe de notification {group_id} introuvable")
                return notifications_created
        
        if recipient_ids:
            recipients.extend(User.objects.filter(id__in=recipient_ids))
        
        if not recipients and group_id is None and not recipient_ids:
            logger.error("Aucun destinataire spécifié")
            return notifications_created
        
        # Récupérer le template si fourni
        template = None
        if template_id:
            try:
                template = NotificationTemplate.objects.get(id=template_id, is_active=True)
                if not title:
                    title = template.name
                if not message:
                    message = template.message_template
                if not channels:
                    channels = template.channels
            except NotificationTemplate.DoesNotExist:
                logger.error(f"Template {template_id} introuvable")
                return notifications_created
        
        # Définir les canaux par défaut
        if not channels:
            channels = ['websocket', 'in_app']
        
        # Créer les notifications
        for recipient in recipients:
            try:
                # Préparer le contenu
                notification_title = title or "Notification"
                notification_message = message or ""
                
                # Traiter le template avec les variables
                if template and variables:
                    try:
                        from django.template import Template, Context
                        title_template = Template(notification_title)
                        message_template = Template(notification_message)
                        
                        context = Context(variables)
                        notification_title = title_template.render(context)
                        notification_message = message_template.render(context)
                    except Exception as e:
                        logger.warning(f"Erreur traitement template pour {recipient.id}: {e}")
                
                # Créer l'objet de notification
                notification = Notification.objects.create(
                    recipient=recipient,
                    template=template,
                    title=notification_title,
                    message=notification_message,
                    notification_type=notification_type,
                    priority=priority,
                    channels_sent=[],  # Sera rempli lors de l'envoi
                    metadata=variables or {}
                )
                
                # Ajouter la relation de contenu si fournie
                if content_type_id and object_id:
                    try:
                        content_type = ContentType.objects.get_for_id(content_type_id)
                        notification.content_type = content_type
                        notification.object_id = object_id
                        notification.save()
                    except ContentType.DoesNotExist:
                        logger.warning(f"Type de contenu {content_type_id} introuvable")
                
                notifications_created.append(notification)
                
            except Exception as e:
                logger.error(f"Erreur création notification pour {recipient.id}: {e}")
                continue
        
        # Envoyer les notifications via les canaux spécifiés
        if notifications_created and channels:
            NotificationService.send_notifications(notifications_created, channels)
        
        return notifications_created
    
    @staticmethod
    def send_notifications(notifications: List[Notification], channels: List[str]) -> Dict[str, int]:
        """Envoie des notifications via les canaux spécifiés"""
        
        results = {
            'total': len(notifications),
            'sent': 0,
            'failed': 0,
            'by_channel': {}
        }
        
        for channel in channels:
            results['by_channel'][channel] = {
                'sent': 0,
                'failed': 0
            }
        
        for notification in notifications:
            for channel in channels:
                try:
                    success = False
                    
                    if channel == 'websocket':
                        # Envoyer via WebSocket de manière asynchrone
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        message = {
                            'id': str(notification.id),
                            'title': notification.title,
                            'message': notification.message,
                            'type': notification.notification_type,
                            'priority': notification.priority,
                            'timestamp': notification.created_at.isoformat(),
                            'read': notification.read_at is not None
                        }
                        
                        success = loop.run_until_complete(
                            WebSocketService.send_to_user(str(notification.recipient.id), message)
                        )
                        loop.close()
                    
                    elif channel == 'email':
                        success = EmailService.send_notification_email(notification)
                    
                    elif channel == 'sms':
                        success = SMSService.send_notification_sms(notification)
                    
                    elif channel == 'push':
                        success = PushNotificationService.send_notification_push(notification)
                    
                    elif channel == 'in_app':
                        # Les notifications in-app sont stockées et affichées par l'interface
                        notification.mark_as_sent('in_app')
                        success = True
                    
                    if success:
                        results['sent'] += 1
                        results['by_channel'][channel]['sent'] += 1
                    else:
                        results['failed'] += 1
                        results['by_channel'][channel]['failed'] += 1
                
                except Exception as e:
                    logger.error(f"Erreur envoi notification {notification.id} via {channel}: {e}")
                    results['failed'] += 1
                    results['by_channel'][channel]['failed'] += 1
        
        return results
    
    @staticmethod
    def mark_as_read(notification_id: str, user_id: str) -> bool:
        """Marque une notification comme lue"""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient_id=user_id
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
    
    @staticmethod
    def get_user_notifications(
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """Récupère les notifications d'un utilisateur"""
        
        query = Notification.objects.filter(recipient_id=user_id)
        
        if unread_only:
            query = query.filter(read_at__isnull=True)
        
        total = query.count()
        notifications = query.select_related('template', 'content_type')[offset:offset+limit]
        
        return {
            'total': total,
            'notifications': list(notifications.values()),
            'has_more': (offset + limit) < total
        }
    
    @staticmethod
    def get_notification_stats(user_id: str) -> Dict[str, Any]:
        """Récupère les statistiques de notifications d'un utilisateur"""
        
        base_query = Notification.objects.filter(recipient_id=user_id)
        
        # Calculs des statistiques
        total_notifications = base_query.count()
        unread_notifications = base_query.filter(read_at__isnull=True).count()
        
        # Notifications du jour
        today = timezone.now().date()
        sent_today = base_query.filter(created_at__date=today).count()
        
        # Échecs
        failed_notifications = base_query.filter(status='failed').count()
        
        # Par type
        by_type = {}
        for notif_type, _ in Notification.NOTIFICATION_TYPES:
            by_type[notif_type] = base_query.filter(notification_type=notif_type).count()
        
        # Par priorité
        by_priority = {}
        for priority, _ in Notification.PRIORITY_CHOICES:
            by_priority[priority] = base_query.filter(priority=priority).count()
        
        # Par canal
        by_channel = {}
        for channel, _ in NotificationLog.CHANNELS:
            by_channel[channel] = NotificationLog.objects.filter(
                notification__recipient_id=user_id,
                channel=channel,
                status='sent'
            ).count()
        
        # Taux de réponse (notifications lues / total)
        response_rate = (unread_notifications / total_notifications * 100) if total_notifications > 0 else 0
        
        return {
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'sent_today': sent_today,
            'failed_notifications': failed_notifications,
            'by_type': by_type,
            'by_priority': by_priority,
            'by_channel': by_channel,
            'response_rate': round(response_rate, 2)
        }