"""
Management command to create missing user profiles
"""
from django.core.management.base import BaseCommand
from apps.custom_auth.models import User, UserProfile


class Command(BaseCommand):
    help = 'Create missing profiles for users who do not have one'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating missing user profiles...'))
        
        users_without_profile = []
        users_with_profile = 0
        
        for user in User.objects.all():
            try:
                _ = user.profile
                users_with_profile += 1
            except User.profile.RelatedObjectDoesNotExist:
                users_without_profile.append(user)
                
                # Create profile with default values
                UserProfile.objects.create(
                    user=user,
                    role=getattr(user, 'role', 'client'),
                    phone_number='',
                    address=''
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Profile created for {user.username} ({user.email})')
                )
        
        if not users_without_profile:
            self.stdout.write(
                self.style.SUCCESS(f'✅ All {users_with_profile} users already have profiles')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Created {len(users_without_profile)} profiles'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Total users with profiles: {users_with_profile + len(users_without_profile)}'
                )
            )
