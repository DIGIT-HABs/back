import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from apps.auth.models import User

email = "moussa.diop@digit-hab.com"
password = "test123"

try:
    user = User.objects.get(email=email)
    print(f"User found: {user.username}")
    print(f"Password check: {user.check_password(password)}")
    
    if not user.check_password(password):
        print("Fixing password...")
        user.set_password(password)
        user.save()
        print("Password fixed!")
        print(f"New check: {user.check_password(password)}")
    else:
        print("Password is correct!")
        
except User.DoesNotExist:
    print("User not found, creating...")
    user = User.objects.create_user(
        username='agent1',
        email=email,
        password=password,
        first_name='Moussa',
        last_name='Diop',
    )
    if hasattr(user, 'role'):
        user.role = 'agent'
        user.save()
    print(f"User created: {user.username}")

