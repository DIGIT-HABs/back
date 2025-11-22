"""
Permissions pour le système de notifications
Contrôle d'accès granulaire pour les notifications en temps réel
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class CanSendNotification(permissions.BasePermission):
    """Permission pour envoyer des notifications"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Les administrateurs et agents peuvent envoyer des notifications
        return (
            request.user.is_superuser or 
            request.user.is_staff or
            hasattr(request.user, 'profile') and 
            request.user.profile.role in ['agent', 'manager', 'admin']
        )


class CanManageNotificationSettings(permissions.BasePermission):
    """Permission pour gérer les paramètres de notification"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # L'utilisateur peut modifier ses propres paramètres
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Les administrateurs peuvent modifier tous les paramètres
        return request.user.is_superuser or request.user.is_staff


class CanViewNotification(permissions.BasePermission):
    """Permission pour voir les notifications"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # L'utilisateur peut voir ses propres notifications
        if obj.recipient == request.user:
            return True
        
        # Les administrateurs peuvent voir toutes les notifications
        return request.user.is_superuser or request.user.is_staff


class CanManageNotificationTemplate(permissions.BasePermission):
    """Permission pour gérer les modèles de notifications"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Seul les administrateurs peuvent gérer les modèles
        return request.user.is_superuser


class CanCreateNotification(permissions.BasePermission):
    """Permission pour créer des notifications"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Les agents, managers et admins peuvent créer des notifications
        return (
            request.user.is_superuser or 
            request.user.is_staff or
            (hasattr(request.user, 'profile') and 
             request.user.profile.role in ['agent', 'manager', 'admin'])
        )


class IsNotificationRecipient(permissions.BasePermission):
    """Permission pour vérifier que l'utilisateur est le destinataire"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # L'utilisateur peut accéder à ses propres notifications
        return obj.recipient == request.user


class CanManageNotificationGroup(permissions.BasePermission):
    """Permission pour gérer les groupes de notifications"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Les administrateurs et managers peuvent gérer les groupes
        return (
            request.user.is_superuser or 
            request.user.is_staff or
            (hasattr(request.user, 'profile') and 
             request.user.profile.role in ['manager', 'admin'])
        )


class CanViewNotificationLogs(permissions.BasePermission):
    """Permission pour voir les journaux de notifications"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Les administrateurs et agents peuvent voir les logs
        return (
            request.user.is_superuser or 
            request.user.is_staff or
            hasattr(request.user, 'profile')
        )


class CanSubscribeToChannels(permissions.BasePermission):
    """Permission pour s'abonner aux canaux de notification"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Tous les utilisateurs authentifiés peuvent s'abonner
        return True
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # L'utilisateur peut gérer ses propres abonnements
        return obj.user == request.user or request.user.is_superuser


class NotificationPermissionMixin:
    """Mixin pour les permissions communes aux notifications"""
    
    def get_notification_permissions(self, user, obj=None):
        """Retourne les permissions basées sur le rôle de l'utilisateur"""
        if not user or not user.is_authenticated:
            return []
        
        permissions = ['view_notification']
        
        if user.is_superuser or user.is_staff:
            permissions.extend([
                'create_notification',
                'edit_notification', 
                'delete_notification',
                'send_notification',
                'manage_templates',
                'view_logs'
            ])
        elif hasattr(user, 'profile'):
            role = user.profile.role
            if role in ['manager', 'admin']:
                permissions.extend([
                    'create_notification',
                    'edit_notification',
                    'send_notification',
                    'view_logs'
                ])
            elif role == 'agent':
                permissions.extend([
                    'create_notification',
                    'send_notification'
                ])
        
        return permissions