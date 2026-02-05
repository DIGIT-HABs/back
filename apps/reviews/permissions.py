"""
Permissions for reviews app.
"""

from rest_framework import permissions


class IsReviewAuthorOrReadOnly(permissions.BasePermission):
    """
    Permission to allow only review authors to edit/delete their reviews.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access the review."""
        # Read permissions for published reviews
        if request.method in permissions.SAFE_METHODS:
            return obj.is_published or obj.author == request.user or request.user.is_staff
        
        # Write permissions only for author
        return obj.author == request.user


class CanModerateReviews(permissions.BasePermission):
    """
    Permission to allow only agents and staff to moderate reviews.
    """
    
    def has_permission(self, request, view):
        """Check if user can moderate reviews."""
        if not request.user.is_authenticated:
            return False
        
        # Staff and superusers can moderate
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Managers can moderate
        if request.user.role == 'manager':
            return True
        
        return False


class CanRespondToReview(permissions.BasePermission):
    """
    Permission to allow agents to respond to reviews about themselves or their properties.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can respond to this review."""
        user = request.user
        
        if not user.is_authenticated:
            return False
        
        # Staff can respond to any review
        if user.is_staff or user.is_superuser:
            return True
        
        # Agent can respond to reviews about them
        if obj.agent == user:
            return True
        
        # Agent can respond to reviews about their properties
        if obj.property and obj.property.agent == user:
            return True
        
        # Agency manager can respond to reviews for their agency
        if user.role == 'manager':
            user_agency = getattr(user.profile, 'agency', None) if hasattr(user, 'profile') else None
            if user_agency:
                if obj.property and obj.property.agency == user_agency:
                    return True
                if obj.agent:
                    agent_agency = getattr(obj.agent.profile, 'agency', None) if hasattr(obj.agent, 'profile') else None
                    if agent_agency == user_agency:
                        return True
        
        return False


class CanCreateReview(permissions.BasePermission):
    """
    Permission to allow only clients who have completed a reservation to create a review.
    """
    
    def has_permission(self, request, view):
        """Check if user can create a review."""
        if not request.user.is_authenticated:
            return False
        
        # Only clients can create reviews (agents/staff shouldn't review their own work)
        # But we allow any authenticated user for flexibility
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user can review this object."""
        # For now, any authenticated user can create a review
        # Validation of "has completed a reservation" is done in the serializer
        return True


class CanVoteHelpful(permissions.BasePermission):
    """
    Permission to allow authenticated users to vote reviews as helpful.
    """
    
    def has_permission(self, request, view):
        """Check if user can vote."""
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user can vote on this review."""
        # Users cannot vote on their own reviews
        return obj.author != request.user
