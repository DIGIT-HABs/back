import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from apps.auth.models import User

user = User.objects.get(email='moussa.diop@digit-hab.com')
print(f"User: {user.username}")
print(f"Password check: {user.check_password('test123')}")

# Test simple du serializer
from apps.auth.serializers import TokenObtainPairSerializer

data = {'email': 'moussa.diop@digit-hab.com', 'password': 'test123'}
s = TokenObtainPairSerializer(data=data)

print(f"\nIs valid: {s.is_valid()}")
if not s.is_valid():
    print(f"Errors: {s.errors}")
else:
    print("SUCCESS!")

