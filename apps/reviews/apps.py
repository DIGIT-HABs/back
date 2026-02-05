"""
Configuration for reviews app.
"""

from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reviews'
    verbose_name = 'Avis et Notations'
    
    def ready(self):
        """Import signals when app is ready."""
        import apps.reviews.signals  # noqa
