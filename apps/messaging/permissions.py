"""
Permissions for messaging app.
"""

from rest_framework import permissions


class IsConversationParticipant(permissions.BasePermission):
    """
    Permission to check if user is a participant of the conversation.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user is a participant."""
        if hasattr(obj, 'participants'):
            return request.user in obj.participants.all()
        elif hasattr(obj, 'conversation'):
            return request.user in obj.conversation.participants.all()
        return False
