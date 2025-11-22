"""
Apps configuration for CRM module.
"""

from django.apps import AppConfig


class CrmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.crm'
    verbose_name = 'CRM - Gestion Client'
    
    def ready(self):
        """Import signals when the app is ready."""
        import apps.crm.signals