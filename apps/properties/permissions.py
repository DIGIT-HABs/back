"""
Custom permissions for property management.
"""

from rest_framework import permissions
from apps.auth.models import User


class IsPropertyAgentOrOwner(permissions.BasePermission):
    """
    Permission to allow only the agent who created the property or an admin to modify it.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to modify this property."""
        if not request.user.is_authenticated:
            return False
        
        # Admin can do anything
        if request.user.role == 'admin':
            return True
        
        # Agent can only modify their own properties
        if request.user.role == 'agent':
            return obj.agent == request.user
        
        # Clients can only view
        if request.user.role == 'client':
            return request.method in permissions.SAFE_METHODS
        
        return False


class CanViewProperty(permissions.BasePermission):
    """
    Permission to view properties.
    - Admin: can view all properties
    - Agent: can view all properties
    - Client: can view available properties only
    """
    
    def has_permission(self, request, view):
        """Check if user can view properties."""
        if not request.user.is_authenticated:
            return False
        
        if request.user.role in ['admin', 'agent']:
            return True
        
        if request.user.role == 'client':
            # Clients can only view available properties
            if view.action in ['list', 'retrieve']:
                return True
        
        return False


class IsPropertyAgent(permissions.BasePermission):
    """
    Permission for property agents only.
    """
    
    def has_permission(self, request, view):
        """Check if user is an agent."""
        return (request.user.is_authenticated and 
                request.user.role == 'agent')


class IsAdminOrAgent(permissions.BasePermission):
    """
    Permission for admin and agent roles only.
    """
    
    def has_permission(self, request, view):
        """Check if user is admin or agent."""
        return (request.user.is_authenticated and 
                request.user.role in ['admin', 'agent'])


class CanManageVisits(permissions.BasePermission):
    """
    Permission to manage property visits.
    - Admin: can manage all visits
    - Agent: can manage visits for their properties
    - Client: can manage their own visits
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can manage this visit."""
        if not request.user.is_authenticated:
            return False
        
        if request.user.role == 'admin':
            return True
        
        if request.user.role == 'agent':
            return obj.property.agent == request.user
        
        if request.user.role == 'client':
            return obj.client == request.user
        
        return False


class CanCreateVisit(permissions.BasePermission):
    """
    Permission to create property visits.
    - Admin: can create visits
    - Agent: can create visits for their properties
    - Client: can create visits for available properties
    """
    
    def has_permission(self, request, view):
        """Check if user can create visits."""
        if not request.user.is_authenticated:
            return False
        
        if request.user.role in ['admin', 'agent', 'client']:
            return True
        
        return False


class CanUploadDocuments(permissions.BasePermission):
    """
    Permission to upload property documents.
    - Admin: can upload for all properties
    - Agent: can upload for their properties
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can upload documents for this property."""
        if not request.user.is_authenticated:
            return False
        
        if request.user.role == 'admin':
            return True
        
        if request.user.role == 'agent':
            return obj.agent == request.user
        
        return False


class CanUploadImages(permissions.BasePermission):
    """
    Permission to upload property images.
    - Admin: can upload for all properties
    - Agent: can upload for their properties
    - Client: can upload documents but not images
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can upload images for this property."""
        if not request.user.is_authenticated:
            return False
        
        if request.user.role == 'admin':
            return True
        
        if request.user.role == 'agent':
            return obj.agent == request.user
        
        return False