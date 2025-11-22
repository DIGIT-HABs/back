from django.apps import AppConfig


class PropertiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.properties'
    verbose_name = 'Properties & Real Estate'
    
    def ready(self):
        """Import signals when the app is ready."""
        import apps.properties.signals