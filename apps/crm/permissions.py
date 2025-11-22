"""
Custom permissions for CRM management.
"""

from rest_framework import permissions
from apps.auth.models import User


class IsClientOrOwner(permissions.BasePermission):
    """
    Permission to allow clients to access their own data or agents/admins to access all client data.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access this object."""
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Admin can access everything
        if user.role == 'admin':
            return True
        
        # Clients can only access their own data
        if user.role == 'client':
            if hasattr(obj, 'user'):
                return obj.user == user
            elif hasattr(obj, 'client'):
                return obj.client == user
        
        # Agents can access data for their clients
        if user.role == 'agent':
            if hasattr(obj, 'user') and obj.user.role == 'client':
                return obj.user.agency == user.agency
            elif hasattr(obj, 'client'):
                return obj.client.agency == user.agency
        
        return False


class IsAgentOrAdmin(permissions.BasePermission):
    """
    Permission for admin and agent roles only.
    """
    
    def has_permission(self, request, view):
        """Check if user is admin or agent."""
        return (request.user.is_authenticated and 
                request.user.role in ['admin', 'agent'])


class CanManageClientProfile(permissions.BasePermission):
    """
    Permission to manage client profiles.
    - Admin: can manage all client profiles
    - Agent: can manage profiles for their agency's clients
    - Client: can manage their own profile
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can manage this client profile."""
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Admin can manage all profiles
        if user.role == 'admin':
            return True
        
        # Client can manage their own profile
        if user.role == 'client':
            return obj.user == user
        
        # Agent can manage profiles for their agency's clients
        if user.role == 'agent':
            return obj.user.agency == user.agency
        
        return False


class CanManageLeads(permissions.BasePermission):
    """
    Permission to manage leads.
    - Admin: can manage all leads
    - Agent: can manage leads assigned to them or in their agency
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can manage this lead."""
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Admin can manage all leads
        if user.role == 'admin':
            return True
        
        # Agent can manage leads in their agency
        if user.role == 'agent':
            return obj.agency == user.agency
        
        return False
    
    def has_permission(self, request, view):
        """Check if user can access lead endpoints."""
        if not request.user.is_authenticated:
            return False
        
        # Admin and agents can access lead endpoints
        return request.user.role in ['admin', 'agent']


class CanCreateLead(permissions.BasePermission):
    """
    Permission to create leads.
    - Admin: can create leads for any agency
    - Agent: can create leads for their agency
    """
    
    def has_permission(self, request, view):
        """Check if user can create leads."""
        if not request.user.is_authenticated:
            return False
        
        if request.user.role == 'admin':
            return True
        
        if request.user.role == 'agent':
            return True  # Agents can create leads for their agency
        
        return False


class CanAssignLeads(permissions.BasePermission):
    """
    Permission to assign leads to agents.
    - Admin: can assign leads to any agent
    - Agent: cannot assign leads to others
    """
    
    def has_permission(self, request, view):
        """Check if user can assign leads."""
        if not request.user.is_authenticated:
            return False
        
        # Only admin can assign leads to agents
        return request.user.role == 'admin'


class CanAccessPropertyInterests(permissions.BasePermission):
    """
    Permission to access property interests.
    - Admin: can access all property interests
    - Agent: can access interests for their agency's clients
    - Client: can access their own interests
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access this property interest."""
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Admin can access all interests
        if user.role == 'admin':
            return True
        
        # Client can access their own interests
        if user.role == 'client':
            return obj.client == user
        
        # Agent can access interests for their agency's clients
        if user.role == 'agent':
            return obj.client.agency == user.agency
        
        return False


class CanManageInteractions(permissions.BasePermission):
    """
    Permission to manage client interactions.
    - Admin: can manage all interactions
    - Agent: can manage interactions for their clients
    - Client: can view their own interactions
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can manage this interaction."""
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Admin can manage all interactions
        if user.role == 'admin':
            return True
        
        # Agent can manage interactions for their clients
        if user.role == 'agent':
            return (obj.agent == user or 
                   (obj.client.agency == user.agency and user.role == 'agent'))
        
        # Client can only view (not modify) their own interactions
        if user.role == 'client':
            return obj.client == user
        
        return False


class CanCreateInteraction(permissions.BasePermission):
    """
    Permission to create client interactions.
    - Admin: can create interactions for any client
    - Agent: can create interactions for their clients
    - Client: can create interactions for themselves
    """
    
    def has_permission(self, request, view):
        """Check if user can create interactions."""
        if not request.user.is_authenticated:
            return False
        
        # All authenticated users can create interactions
        return True


class CanAccessMatchingResults(permissions.BasePermission):
    """
    Permission to access property matching results.
    - Admin: can access all matching results
    - Agent: can access matching for their clients
    - Client: can access their own matching results
    """
    
    def has_permission(self, request, view):
        """Check if user can access matching results."""
        if not request.user.is_authenticated:
            return False
        
        # All roles can access matching results for appropriate scope
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access this specific matching result."""
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Admin can access all matching results
        if user.role == 'admin':
            return True
        
        # Client can access their own matching results
        if user.role == 'client':
            if hasattr(obj, 'client'):
                return obj.client == user
            elif hasattr(obj, 'user'):
                return obj.user == user
        
        # Agent can access matching for their clients
        if user.role == 'agent':
            if hasattr(obj, 'client'):
                return obj.client.agency == user.agency
            elif hasattr(obj, 'user'):
                return obj.user.agency == user.agency
        
        return False


class CanViewDashboard(permissions.BasePermission):
    """
    Permission to view dashboard information.
    - Admin: can view all dashboard data
    - Agent: can view dashboard for their clients
    - Client: can view their own dashboard
    """
    
    def has_permission(self, request, view):
        """Check if user can view dashboard."""
        if not request.user.is_authenticated:
            return False
        
        return request.user.role in ['admin', 'agent', 'client']


class CanConvertLead(permissions.BasePermission):
    """
    Permission to convert leads to clients.
    - Admin: can convert any lead
    - Agent: can convert leads from their agency
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can convert this lead."""
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Admin can convert any lead
        if user.role == 'admin':
            return True
        
        # Agent can convert leads from their agency
        if user.role == 'agent':
            return obj.agency == user.agency
        
        return False