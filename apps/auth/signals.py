"""
Signals for authentication app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import UserProfile, Agency

User = get_user_model()

# Licence utilisée pour l'agence "par défaut" des clients (inscription publique)
DEFAULT_CLIENTS_AGENCY_LICENSE = "DEFAULT-CLIENTS"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created. Les clients vont dans une agence par défaut, les agents dans la première agence « réelle »."""
    if created:
        try:
            profile = UserProfile.objects.get(user=instance)
        except UserProfile.DoesNotExist:
            role = getattr(instance, 'role', 'client')
            if role == 'client':
                # Clients : agence dédiée "par défaut" (ne pas les attacher aux agences des agents)
                agency, _ = Agency.objects.get_or_create(
                    license_number=DEFAULT_CLIENTS_AGENCY_LICENSE,
                    defaults={
                        'name': 'Agence par défaut (clients)',
                        'email': 'clients@default.local',
                        'phone': '',
                        'address_line1': 'N/A',
                        'city': 'Dakar',
                        'postal_code': '',
                        'country': 'Sénégal',
                        'subscription_start': timezone.now(),
                        'subscription_end': timezone.now() + timezone.timedelta(days=3650),
                    }
                )
            else:
                # Agent ou admin : première agence "réelle" (hors agence par défaut clients)
                agency = Agency.objects.exclude(license_number=DEFAULT_CLIENTS_AGENCY_LICENSE).first()
                if not agency:
                    agency = Agency.objects.first()
                if not agency:
                    user_phone = getattr(instance, 'phone', None) or ""
                    agency = Agency.objects.create(
                        name="Default Agency",
                        email=instance.email,
                        phone=user_phone,
                        address_line1="Default Address",
                        city="Dakar",
                        postal_code="10000",
                        country="Sénégal",
                        license_number="DEFAULT-LICENSE",
                        subscription_start=timezone.now(),
                        subscription_end=timezone.now() + timezone.timedelta(days=30),
                    )
            UserProfile.objects.create(user=instance, agency=agency)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved."""
    # Temporarily disabled to prevent cascading saves
    return
    
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=User)
def update_last_activity(sender, instance, created, **kwargs):
    """Update last activity when user logs in."""
    # Temporarily disabled - causes issues with admin login
    return
    
    if not created and instance.is_authenticated:
        if hasattr(instance, '_update_activity'):
            # Avoid infinite loops
            delattr(instance, '_update_activity')
        else:
            instance._update_activity = True
            instance.update_last_activity()
            delattr(instance, '_update_activity')