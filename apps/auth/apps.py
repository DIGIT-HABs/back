from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.auth'
    label = 'custom_auth'
    verbose_name = 'Authentication & Users'
    
    def ready(self):
        """Import signals when the app is ready."""
        import apps.auth.signals