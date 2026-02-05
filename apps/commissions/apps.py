from django.apps import AppConfig


class CommissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.commissions'
    verbose_name = 'Commissions & Payments'
    
    def ready(self):
        """Import signals when the app is ready."""
        # import apps.commissions.signals  # Uncomment when signals are created
