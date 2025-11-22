"""
Models for favorites management.
"""

import uuid
from django.db import models
from django.utils import timezone
from apps.auth.models import User
from apps.properties.models import Property


class Favorite(models.Model):
    """User's favorite properties."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='favorited_by')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'favorites'
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        ordering = ['-created_at']
        unique_together = ['user', 'property']  # Un utilisateur ne peut ajouter qu'une fois un bien
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['property']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.property.title}"

