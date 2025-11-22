"""
Views pour le système de notifications en temps réel
API REST avec Django REST Framework
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    Notification, NotificationTemplate, UserNotificationSetting,
    NotificationGroup, NotificationLog, NotificationSubscription
)
from .serializers import (
    NotificationSerializer, NotificationCreateSerializer,
    NotificationTemplateSerializer, UserNotificationSettingSerializer,
    NotificationGroupSerializer, NotificationLogSerializer,
    NotificationSubscriptionSerializer, NotificationStatsSerializer
)
from .permissions import (
    CanSendNotification, CanManageNotificationSettings, CanViewNotification,
    CanManageNotificationTemplate, CanManageNotificationGroup,
    CanViewNotificationLogs, CanSubscribeToChannels
)
from .services import NotificationService

User = get_user_model()


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des notifications"""
    
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, CanViewNotification]
    
    def get_queryset(self):
        """Retourne les notifications de l'utilisateur courant"""
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related(
            'template', 'content_type', 'group'
        ).prefetch_related('logs')
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer
    
    def perform_create(self, serializer):
        """Crée une nouvelle notification"""
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Marque une notification comme lue"""
        notification = self.get_object()
        
        if notification.recipient != request.user:
            return Response(
                {'error': 'Vous ne pouvez marquer que vos propres notifications comme lues'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if notification.mark_as_read():
            return Response({'message': 'Notification marquée comme lue'})
        else:
            return Response(
                {'error': 'Impossible de marquer la notification comme lue'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Marque toutes les notifications non lues comme lues"""
        updated_count = Notification.objects.filter(
            recipient=request.user,
            read_at__isnull=True
        ).update(read_at=timezone.now(), status='read')
        
        return Response({
            'message': f'{updated_count} notifications marquées comme lues'
        })
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Retourne uniquement les notifications non lues"""
        notifications = self.get_queryset().filter(read_at__isnull=True)
        
        page = self.paginate_queryset(notifications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques de notifications"""
        stats = NotificationService.get_notification_stats(str(request.user.id))
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Retourne les notifications récentes"""
        days = request.query_params.get('days', 7)
        try:
            days = int(days)
        except ValueError:
            days = 7
        
        from django.utils import timezone
        from datetime import timedelta
        
        since = timezone.now() - timedelta(days=days)
        notifications = self.get_queryset().filter(created_at__gte=since)
        
        page = self.paginate_queryset(notifications.order_by('-created_at'))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def create_notification(self, request):
        """Crée et envoie une nouvelle notification"""
        self.permission_classes = [IsAuthenticated, CanSendNotification]
        self.check_permissions(request)
        
        serializer = NotificationCreateSerializer(data=request.data)
        if serializer.is_valid():
            notifications = NotificationService.create_notification(**serializer.validated_data)
            
            if notifications:
                result_serializer = NotificationSerializer(notifications, many=True)
                return Response({
                    'message': f'{len(notifications)} notification(s) créée(s)',
                    'notifications': result_serializer.data
                })
            else:
                return Response(
                    {'error': 'Aucune notification créée'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Retourne les journaux d'une notification"""
        notification = self.get_object()
        
        # Vérifier les permissions
        if not (request.user.is_superuser or 
                request.user == notification.recipient or
                notification.recipient.has_perm('notifications.view_notification_logs')):
            return Response(
                {'error': 'Permissions insuffisantes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logs = notification.logs.all()
        serializer = NotificationLogSerializer(logs, many=True)
        return Response(serializer.data)


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des modèles de notifications"""
    
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated, CanManageNotificationTemplate]
    
    def get_queryset(self):
        """Retourne les modèles de notifications"""
        return NotificationTemplate.objects.filter(is_active=True)
    
    def perform_create(self, serializer):
        """Crée un nouveau modèle"""
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Retourne les modèles par type"""
        template_type = request.query_params.get('type')
        if not template_type:
            return Response(
                {'error': 'Type de modèle requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        templates = self.get_queryset().filter(template_type=template_type)
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def channels(self, request):
        """Retourne la liste des canaux disponibles"""
        channels = ['websocket', 'email', 'sms', 'push', 'in_app']
        return Response({'channels': channels})


class UserNotificationSettingViewSet(viewsets.ModelViewSet):
    """ViewSet pour les paramètres de notification utilisateur"""
    
    serializer_class = UserNotificationSettingSerializer
    permission_classes = [IsAuthenticated, CanManageNotificationSettings]
    
    def get_queryset(self):
        """Retourne les paramètres de l'utilisateur courant"""
        if self.request.user.is_superuser:
            return UserNotificationSetting.objects.all()
        return UserNotificationSetting.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Retourne les paramètres de l'utilisateur courant"""
        if self.request.user.is_superuser and 'pk' in self.kwargs:
            return UserNotificationSetting.objects.get(user_id=self.kwargs['pk'])
        
        # Retourner ou créer les paramètres de l'utilisateur courant
        setting, created = UserNotificationSetting.objects.get_or_create(
            user=self.request.user
        )
        return setting
    
    @action(detail=False, methods=['get'])
    def my_settings(self, request):
        """Retourne les paramètres de l'utilisateur courant"""
        setting = self.get_object()
        serializer = self.get_serializer(setting)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_my_settings(self, request):
        """Met à jour les paramètres de l'utilisateur courant"""
        setting = self.get_object()
        serializer = self.get_serializer(setting, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Paramètres mis à jour',
                'settings': serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def test_notification(self, request):
        """Envoie une notification de test"""
        setting = self.get_object()
        
        # Créer une notification de test
        test_notification = NotificationService.create_notification(
            recipient_ids=[str(request.user.id)],
            title="Notification de test",
            message="Ceci est un message de test pour vérifier vos paramètres de notification.",
            notification_type='info',
            channels=['websocket', 'in_app']  # Canaux par défaut pour le test
        )
        
        if test_notification:
            return Response({
                'message': 'Notification de test envoyée',
                'notification_id': str(test_notification[0].id)
            })
        else:
            return Response(
                {'error': 'Impossible d\'envoyer la notification de test'},
                status=status.HTTP_400_BAD_REQUEST
            )


class NotificationGroupViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des groupes de notifications"""
    
    serializer_class = NotificationGroupSerializer
    permission_classes = [IsAuthenticated, CanManageNotificationGroup]
    
    def get_queryset(self):
        """Retourne les groupes de notifications"""
        if self.request.user.is_superuser:
            return NotificationGroup.objects.all()
        return NotificationGroup.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def my_groups(self, request):
        """Retourne les groupes de l'utilisateur"""
        groups = self.get_queryset().filter(users=request.user)
        serializer = self.get_serializer(groups, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_user(self, request, pk=None):
        """Ajoute un utilisateur à un groupe"""
        group = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'ID utilisateur requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            group.users.add(user)
            return Response({'message': 'Utilisateur ajouté au groupe'})
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_user(self, request, pk=None):
        """Retire un utilisateur d'un groupe"""
        group = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'ID utilisateur requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            group.users.remove(user)
            return Response({'message': 'Utilisateur retiré du groupe'})
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def send_notification(self, request, pk=None):
        """Envoie une notification à tout un groupe"""
        group = self.get_object()
        
        # Vérifier les permissions
        if not (request.user.is_superuser or request.user.is_staff):
            return Response(
                {'error': 'Permissions insuffisantes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = NotificationCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Ajouter le groupe aux données validées
            data = serializer.validated_data.copy()
            data['group_id'] = str(group.id)
            
            notifications = NotificationService.create_notification(**data)
            
            if notifications:
                return Response({
                    'message': f'{len(notifications)} notification(s) envoyée(s) au groupe {group.name}',
                    'count': len(notifications)
                })
            else:
                return Response(
                    {'error': 'Aucune notification créée'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet en lecture seule pour les journaux de notifications"""
    
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated, CanViewNotificationLogs]
    
    def get_queryset(self):
        """Retourne les journaux de notifications"""
        if self.request.user.is_superuser:
            return NotificationLog.objects.all()
        
        # Seuls les journaux des notifications de l'utilisateur
        return NotificationLog.objects.filter(
            notification__recipient=self.request.user
        )
    
    @action(detail=False, methods=['get'])
    def my_logs(self, request):
        """Retourne les journaux des notifications de l'utilisateur"""
        logs = self.get_queryset().order_by('-created_at')[:100]  # Limite à 100
        
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)


class NotificationSubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des abonnements aux canaux"""
    
    serializer_class = NotificationSubscriptionSerializer
    permission_classes = [IsAuthenticated, CanSubscribeToChannels]
    
    def get_queryset(self):
        """Retourne les abonnements de l'utilisateur"""
        return NotificationSubscription.objects.filter(
            user=self.request.user
        )
    
    def perform_create(self, serializer):
        """Crée un nouvel abonnement"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_subscriptions(self, request):
        """Retourne les abonnements de l'utilisateur"""
        subscriptions = self.get_queryset()
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available_channels(self, request):
        """Retourne les canaux disponibles pour l'abonnement"""
        channels = {
            'user': 'Canal personnel (notifications utilisateur)',
            'group': 'Canal de groupe (notifications de groupe)',
            'property': 'Canal propriété (notifications liées aux propriétés)',
            'reservation': 'Canal réservation (notifications liées aux réservations)'
        }
        return Response({'channels': channels})
    
    @action(detail=True, methods=['post'])
    def refresh(self, request, pk=None):
        """Actualise un abonnement (met à jour last_seen)"""
        subscription = self.get_object()
        subscription.last_seen = timezone.now()
        subscription.save()
        
        return Response({'message': 'Abonnement actualisé'})
    
    @action(detail=False, methods=['post'])
    def join_property_channel(self, request):
        """Abonne l'utilisateur au canal d'une propriété"""
        property_id = request.data.get('property_id')
        
        if not property_id:
            return Response(
                {'error': 'ID de propriété requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que l'utilisateur a accès à la propriété
        try:
            from apps.properties.models import Property
            property_obj = Property.objects.get(id=property_id)
            
            # L'utilisateur doit être agent ou propriétaire de la propriété
            user_profile = getattr(request.user, 'profile', None)
            if not user_profile or (property_obj.agent != request.user and property_obj.owner != request.user):
                return Response(
                    {'error': 'Accès refusé à cette propriété'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
        except Property.DoesNotExist:
            return Response(
                {'error': 'Propriété introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Créer l'abonnement
        subscription, created = NotificationSubscription.objects.get_or_create(
            user=request.user,
            channel_name=f"property_{property_id}",
            channel_type='property',
            content_type_id=ContentType.objects.get_for_model(property_obj).id,
            object_id=property_id
        )
        
        if created:
            return Response({'message': 'Abonnement créé'})
        else:
            subscription.is_active = True
            subscription.save()
            return Response({'message': 'Abonnement activé'})
    
    @action(detail=False, methods=['post'])
    def leave_property_channel(self, request):
        """Désabonne l'utilisateur du canal d'une propriété"""
        property_id = request.data.get('property_id')
        
        if not property_id:
            return Response(
                {'error': 'ID de propriété requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated = NotificationSubscription.objects.filter(
            user=request.user,
            channel_name=f"property_{property_id}",
            channel_type='property'
        ).update(is_active=False)
        
        if updated:
            return Response({'message': 'Abonnement désactivé'})
        else:
            return Response(
                {'error': 'Abonnement introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )