"""
Favorites app configuration.
"""

from django.apps import AppConfig


class FavoritesConfig(AppConfig):
    """Configuration for the Favorites app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.favorites'
    verbose_name = 'Favorites'

