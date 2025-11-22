"""
Permissions for reservations management.
"""

from rest_framework import permissions
from apps.auth.models import User


class IsReservationOwnerOrAgent(permissions.BasePermission):
    """
    Permission to allow only reservation owners or assigned agents to access/modify.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access the reservation."""
        user = request.user
        
        # Staff and superusers have all permissions
        if user.is_staff or user.is_superuser:
            return True
        
        # Check if user is the assigned agent
        if obj.assigned_agent and obj.assigned_agent == user:
            return True
        
        # Check if user is the client who made the reservation
        if obj.client_profile and obj.client_profile.user == user:
            return True
        
        # Check agency-level access (if user's agency matches property's agency)
        user_agency = getattr(user.profile, 'agency', None) if hasattr(user, 'profile') else None
        if user_agency and obj.property.agency == user_agency:
            return True
        
        return False


class CanManageReservations(permissions.BasePermission):
    """
    Permission to allow agents and staff to manage all reservations.
    """
    
    def has_permission(self, request, view):
        """Check if user can manage reservations."""
        user = request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return False
        
        # Staff and superusers have all permissions
        if user.is_staff or user.is_superuser:
            return True
        
        # Agents can manage reservations
        if user.role in ['agent', 'manager']:
            return True
        
        return False


class CanViewAllReservations(permissions.BasePermission):
    """
    Permission to allow viewing all reservations within user's scope.
    """
    
    def has_permission(self, request, view):
        """Check if user can view reservations."""
        user = request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return False
        
        # Staff and superusers can view all
        if user.is_staff or user.is_superuser:
            return True
        
        # Agents can view reservations for their agency
        if user.role in ['agent', 'manager']:
            return True
        
        # Clients can only view their own reservations
        if user.role == 'client':
            return True
        
        return False


class CanAccessPaymentData(permissions.BasePermission):
    """
    Permission to access payment-related data.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access payment data."""
        user = request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return False
        
        # Staff and superusers have all permissions
        if user.is_staff or user.is_superuser:
            return True
        
        # Check reservation access first
        reservation = obj.reservation if hasattr(obj, 'reservation') else obj
        
        # Assigned agent can access payment data
        if reservation.assigned_agent and reservation.assigned_agent == user:
            return True
        
        # Client can access their own payment data
        if reservation.client_profile and reservation.client_profile.user == user:
            return True
        
        # Agency staff can access payments for their agency's properties
        user_agency = getattr(user.profile, 'agency', None) if hasattr(user, 'profile') else None
        if user_agency and reservation.property.agency == user_agency:
            return True
        
        return False


class CanProcessPayments(permissions.BasePermission):
    """
    Permission to process and manage payments.
    """
    
    def has_permission(self, request, view):
        """Check if user can process payments."""
        user = request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return False
        
        # Staff and superusers can process payments
        if user.is_staff or user.is_superuser:
            return True
        
        # Managers can process payments
        if user.role == 'manager':
            return True
        
        # Agents can process payments for their assigned reservations
        if user.role == 'agent':
            return True
        
        return False


class IsAgencyMember(permissions.BasePermission):
    """
    Permission to check if user belongs to the same agency as the property.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user belongs to the same agency as the property."""
        user = request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return False
        
        # Staff and superusers have all permissions
        if user.is_staff or user.is_superuser:
            return True
        
        # Get user's agency
        user_agency = getattr(user.profile, 'agency', None) if hasattr(user, 'profile') else None
        
        # Get property's agency
        if hasattr(obj, 'property'):
            property_agency = obj.property.agency
        elif hasattr(obj, 'agency'):
            property_agency = obj.agency
        else:
            return False
        
        # Check if agencies match
        return user_agency == property_agency


class CanScheduleVisits(permissions.BasePermission):
    """
    Permission to schedule and manage visits.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can schedule visits for this property."""
        user = request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return False
        
        # Staff and superusers can schedule visits
        if user.is_staff or user.is_superuser:
            return True
        
        # Agent assigned to the property can schedule visits
        if obj.property.agent == user:
            return True
        
        # Any agent from the same agency can schedule visits
        user_agency = getattr(user.profile, 'agency', None) if hasattr(user, 'profile') else None
        if user_agency and obj.property.agency == user_agency and user.role in ['agent', 'manager']:
            return True
        
        # Clients can schedule visits for available properties
        if user.role == 'client' and obj.property.status == 'available':
            return True
        
        return False


class CanModifyReservationStatus(permissions.BasePermission):
    """
    Permission to modify reservation status.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can modify reservation status."""
        user = request.user
        
        # Check if user is authenticated
        if not user.is_authenticated:
            return False
        
        # Staff and superusers can modify any status
        if user.is_staff or user.is_superuser:
            return True
        
        # Assigned agent can modify status
        if obj.assigned_agent and obj.assigned_agent == user:
            return True
        
        # Agency managers can modify status for their agency's properties
        user_agency = getattr(user.profile, 'agency', None) if hasattr(user, 'profile') else None
        if user_agency and obj.property.agency == user_agency and user.role == 'manager':
            return True
        
        # Clients can only cancel their own reservations
        if hasattr(request, 'method') and request.method in ['PUT', 'PATCH']:
            if obj.client_profile and obj.client_profile.user == user:
                return request.data.get('status') == 'cancelled'
        
        return False


class ReadOnly(permissions.BasePermission):
    """
    Permission that only allows read operations.
    """
    
    def has_permission(self, request, view):
        """Allow read operations for authenticated users."""
        return request.method in permissions.SAFE_METHODS and request.user.is_authenticated