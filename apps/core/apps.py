from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core & Configuration'
    
    def ready(self):
        """Import signals when the app is ready."""
        import apps.core.signals