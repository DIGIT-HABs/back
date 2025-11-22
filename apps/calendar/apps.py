"""
Application de calendrier intelligent
Planification automatique des visites avec algorithmes d'optimisation
"""

from django.apps import AppConfig


class CalendarConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.calendar'
    verbose_name = 'Calendar'

    def ready(self):
        """Connecter les signaux lors de l'initialisation"""
        import apps.calendar.signals