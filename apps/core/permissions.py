"""
Custom permissions for core app.
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to modify, others to read.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.is_superuser)
        )
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.is_superuser)
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners or admin to edit objects.
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Admin users can do everything
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user is owner
        if hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow staff users to modify, others to read.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )


class IsSystemAdmin(permissions.BasePermission):
    """
    Custom permission to only allow system administrators.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_superuser
        )


class CanManageFiles(permissions.BasePermission):
    """
    Custom permission for file management operations.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Staff and superusers can manage all files
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Regular users can upload files
        if request.method in ['POST']:
            return True
        
        # Regular users can only access their own files
        if request.method in ['GET', 'PUT', 'PATCH', 'DELETE']:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Admin users can manage all files
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Users can only access their own files
        if hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == request.user
        
        return False


class CanViewSystemLogs(permissions.BasePermission):
    """
    Custom permission to view system logs.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can view all logs
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Users can view their own activity logs
        if request.method in ['GET'] and view.action == 'list':
            return True
        
        return False


class CanManageNotifications(permissions.BasePermission):
    """
    Custom permission to manage notifications.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Create notification requires staff permissions
        if request.method in ['POST']:
            return request.user.is_staff or request.user.is_superuser
        
        # Read operations allowed for all authenticated users
        if request.method in ['GET']:
            return True
        
        # Update operations allowed for own notifications
        if request.method in ['PUT', 'PATCH']:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Users can only modify their own notifications
        if hasattr(obj, 'recipient_id'):
            return obj.recipient_id == str(request.user.id)
        
        return False


class CanAccessSystemStats(permissions.BasePermission):
    """
    Custom permission to access system statistics.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can access all statistics
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Regular users can access basic statistics
        if request.method in ['GET']:
            return True
        
        return False


class IsPublicConfiguration(permissions.BasePermission):
    """
    Custom permission for public configuration access.
    """
    
    def has_permission(self, request, view):
        # Public configurations are accessible to all
        if hasattr(view, 'action') and view.action == 'public':
            return True
        
        # Other operations require authentication
        return request.user and request.user.is_authenticated