"""
Custom permissions for authentication app.
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the snippet.
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif isinstance(obj, UserModel):
            return obj == request.user
        else:
            return False


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or request.user.is_superuser)
        )


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsAgencyMember(permissions.BasePermission):
    """
    Custom permission to only allow members of the same agency.
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Allow superusers and staff
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user is member of the same agency as the object
        if hasattr(obj, 'agency'):
            user_agency = getattr(request.user.profile, 'agency', None)
            return obj.agency == user_agency
        elif hasattr(obj, 'user'):
            user_agency = getattr(request.user.profile, 'agency', None)
            obj_user_agency = getattr(obj.user.profile, 'agency', None)
            return user_agency == obj_user_agency
        
        return False


class IsSameAgencyMember(permissions.BasePermission):
    """
    Custom permission to only allow members of the same agency.
    For listing operations, checks that the user can see objects from their agency.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow superusers and staff
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # For admin operations, check that the user has access to the agency
        if hasattr(request.user, 'profile'):
            return True  # User has a profile, so they can access
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Allow superusers and staff
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check agency membership
        user_agency = getattr(request.user.profile, 'agency', None)
        if not user_agency:
            return False
        
        if hasattr(obj, 'agency'):
            return obj.agency == user_agency
        elif hasattr(obj, 'user'):
            obj_user_agency = getattr(obj.user.profile, 'agency', None)
            return obj_user_agency == user_agency
        
        return False


class IsVerifiedUser(permissions.BasePermission):
    """
    Custom permission to only allow verified users.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_verified
        )


class CanManageUsers(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage other users.
    This includes admins and agency managers.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can manage all users
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user is an agency manager
        if hasattr(request.user, 'profile'):
            # Agency managers can manage users in their agency
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can manage all users
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user can manage the specific object
        if hasattr(obj, 'user'):
            user_agency = getattr(request.user.profile, 'agency', None)
            obj_user_agency = getattr(obj.user.profile, 'agency', None)
            return user_agency == obj_user_agency
        elif isinstance(obj, UserModel):
            user_agency = getattr(request.user.profile, 'agency', None)
            obj_user_agency = getattr(obj.profile, 'agency', None)
            return user_agency == obj_user_agency
        
        return False


class CanChangePassword(permissions.BasePermission):
    """
    Custom permission to allow users to change their own password.
    """
    
    def has_object_permission(self, request, view, obj):
        # Users can change their own password
        return obj == request.user


class IsActiveUser(permissions.BasePermission):
    """
    Custom permission to only allow active users.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_active
        )


class ReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow read operations.
    """
    
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsSelfOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow users to modify their own data or admins.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if not request.user.is_authenticated:
            return False
        
        # Allow superusers and staff
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Allow users to modify their own data
        if isinstance(obj, UserModel):
            return obj == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False