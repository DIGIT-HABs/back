"""
Permissions pour le système de calendrier intelligent
Contrôle d'accès granulaire pour la planification automatique
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class CanAccessCalendar(permissions.BasePermission):
    """Permission pour accéder au calendrier"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Les utilisateurs avec profil peuvent accéder au calendrier
        return hasattr(request.user, 'profile')


class CanScheduleVisits(permissions.BasePermission):
    """Permission pour planifier des visites"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Les agents, managers et admins peuvent planifier
        return (
            request.user.is_superuser or 
            request.user.is_staff or
            (hasattr(request.user, 'profile') and 
             request.user.profile.role in ['agent', 'manager', 'admin'])
        )


class CanManageOwnSchedule(permissions.BasePermission):
    """Permission pour gérer son propre planning"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # L'utilisateur peut gérer son propre planning
        return obj.agent == request.user or obj.user == request.user


class CanViewAgentSchedule(permissions.BasePermission):
    """Permission pour voir le planning d'un agent"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # L'agent peut voir son propre planning
        if obj.agent == request.user:
            return True
        
        # Les administrateurs et managers peuvent voir tous les plannings
        return (
            request.user.is_superuser or 
            request.user.is_staff or
            (hasattr(request.user, 'profile') and 
             request.user.profile.role in ['manager', 'admin'])
        )


class CanManageTimeSlots(permissions.BasePermission):
    """Permission pour gérer les créneaux horaires"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # L'utilisateur peut gérer ses propres créneaux
        if obj.user == request.user:
            return True
        
        # Les administrateurs peuvent gérer tous les créneaux
        return request.user.is_superuser or request.user.is_staff


class CanOverrideSchedules(permissions.BasePermission):
    """Permission pour modifier les planifications automatiques"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Seuls les managers et admins peuvent overrides
        return (
            request.user.is_superuser or 
            request.user.is_staff or
            (hasattr(request.user, 'profile') and 
             request.user.profile.role in ['manager', 'admin'])
        )


class CanOptimizeSchedules(permissions.BasePermission):
    """Permission pour optimiser les plannings"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Les agents et au-dessus peuvent optimiser
        return (
            request.user.is_superuser or 
            request.user.is_staff or
            (hasattr(request.user, 'profile') and 
             request.user.profile.role in ['agent', 'manager', 'admin'])
        )


class CanViewScheduleMetrics(permissions.BasePermission):
    """Permission pour voir les métriques de planification"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # L'agent peut voir ses propres métriques
        if obj.agent == request.user:
            return True
        
        # Les administrateurs et managers peuvent voir toutes les métriques
        return request.user.is_superuser or request.user.is_staff


class CanManageWorkingHours(permissions.BasePermission):
    """Permission pour gérer les horaires de travail"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # L'utilisateur peut gérer ses propres horaires
        if obj.user == request.user:
            return True
        
        # Les administrateurs peuvent gérer tous les horaires
        return request.user.is_superuser or request.user.is_staff


class CanResolveConflicts(permissions.BasePermission):
    """Permission pour résoudre les conflits de planning"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Les agents et au-dessus peuvent résoudre les conflits
        return (
            request.user.is_superuser or 
            request.user.is_staff or
            (hasattr(request.user, 'profile') and 
             request.user.profile.role in ['agent', 'manager', 'admin'])
        )


class CanSetSchedulingPreferences(permissions.BasePermission):
    """Permission pour configurer les préférences de planification"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # L'utilisateur peut gérer ses propres préférences
        if obj.user == request.user:
            return True
        
        # Les administrateurs peuvent gérer toutes les préférences
        return request.user.is_superuser or request.user.is_staff


class IsClientOrAuthorized(permissions.BasePermission):
    """Permission pour vérifier que l'utilisateur est le client ou autorisé"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # L'utilisateur est le client
        if obj.client == request.user:
            return True
        
        # L'utilisateur est l'agent assigné
        if obj.agent == request.user:
            return True
        
        # Les administrateurs ont tous les droits
        return request.user.is_superuser or request.user.is_staff


class CanAutoSchedule(permissions.BasePermission):
    """Permission pour la planification automatique"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Seuls les agents configurés pour la planification automatique
        return (
            request.user.is_superuser or 
            request.user.is_staff or
            (hasattr(request.user, 'profile') and 
             request.user.profile.role in ['agent', 'manager', 'admin'])
        )


class CalendarPermissionMixin:
    """Mixin pour les permissions communes du calendrier"""
    
    def get_calendar_permissions(self, user, obj=None):
        """Retourne les permissions basées sur le rôle de l'utilisateur"""
        if not user or not user.is_authenticated:
            return []
        
        permissions = ['view_calendar', 'view_schedule']
        
        if user.is_superuser or user.is_staff:
            permissions.extend([
                'manage_calendar',
                'schedule_visits',
                'manage_time_slots',
                'optimize_schedules',
                'view_metrics',
                'resolve_conflicts',
                'set_preferences',
                'override_schedules'
            ])
        elif hasattr(user, 'profile'):
            role = user.profile.role
            if role in ['manager', 'admin']:
                permissions.extend([
                    'schedule_visits',
                    'optimize_schedules',
                    'view_metrics',
                    'resolve_conflicts',
                    'set_preferences',
                    'override_schedules'
                ])
            elif role == 'agent':
                permissions.extend([
                    'schedule_visits',
                    'optimize_schedules',
                    'manage_time_slots',
                    'set_preferences',
                    'view_metrics'
                ])
        
        return permissions