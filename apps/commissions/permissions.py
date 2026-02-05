"""
Custom permissions for commission management.
"""

from rest_framework import permissions


class CanManageCommissions(permissions.BasePermission):
    """
    Permission to manage commissions.
    - Admin: can manage all commissions
    - Agent: can view their own commissions
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can manage this commission."""
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Admin can manage all commissions
        if user.role == 'admin':
            return True
        
        # Agent can view their own commissions
        if user.role == 'agent':
            return obj.agent == user
        
        return False
    
    def has_permission(self, request, view):
        """Check if user can access commission endpoints."""
        if not request.user.is_authenticated:
            return False
        
        return request.user.role in ['admin', 'agent']


class CanManagePayments(permissions.BasePermission):
    """
    Permission to manage payments.
    - Admin: can manage all payments
    - Agent: can view their own payments
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can manage this payment."""
        if not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Admin can manage all payments
        if user.role == 'admin':
            return True
        
        # Agent can view their own payments
        if user.role == 'agent':
            return obj.agent == user
        
        return False
    
    def has_permission(self, request, view):
        """Check if user can access payment endpoints."""
        if not request.user.is_authenticated:
            return False
        
        return request.user.role in ['admin', 'agent']

