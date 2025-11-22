"""
Signals for authentication app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import UserProfile, Agency

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created."""
    if created:
        # Try to assign to an agency or create a default one
        agency = Agency.objects.first()  # Get first agency or create default
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
                subscription_end=timezone.now() + timezone.timedelta(days=30)
            )
        
        # Create profile if it doesn't exist
        try:
            profile = UserProfile.objects.get(user=instance)
        except UserProfile.DoesNotExist:
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