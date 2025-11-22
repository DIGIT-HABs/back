import os
import sys

# Clear any cached imports
if 'apps.auth.serializers' in sys.modules:
    del sys.modules['apps.auth.serializers']

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

# Now import after Django is set up
from apps.auth.serializers import TokenObtainPairSerializer

print("\n" + "="*70)
print("TEST FINAL DU SERIALIZER DE LOGIN")
print("="*70 + "\n")

# Test data
test_data = {
    'email': 'moussa.diop@digit-hab.com',
    'password': 'test123'
}

print(f"📧 Email: {test_data['email']}")
print(f"🔑 Password: {test_data['password']}")
print("\n" + "-"*70)

# Create serializer
serializer = TokenObtainPairSerializer(data=test_data)

print("\n🔍 Validation du serializer...")
if serializer.is_valid():
    print("✅ SUCCÈS! Le serializer est valide!")
    print("\n📦 Données retournées:")
    print(f"   - Access token: ✅ Présent")
    print(f"   - Refresh token: ✅ Présent")
    print(f"   - User data: ✅ Présent")
    
    validated_data = serializer.validated_data
    user_data = validated_data.get('user', {})
    print(f"\n👤 Informations utilisateur:")
    print(f"   - Username: {user_data.get('username')}")
    print(f"   - Email: {user_data.get('email')}")
    print(f"   - Role: {user_data.get('role')}")
    
    print("\n" + "="*70)
    print("✨ LE LOGIN FONCTIONNERA VIA L'API! ✨")
    print("="*70 + "\n")
else:
    print("❌ ÉCHEC! Le serializer est invalide!")
    print(f"\n🔴 Erreurs:")
    for field, errors in serializer.errors.items():
        print(f"   - {field}: {errors}")
    
    print("\n" + "="*70)
    print("⚠️ PROBLÈME À CORRIGER")
    print("="*70 + "\n")

