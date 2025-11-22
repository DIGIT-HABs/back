import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from apps.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

# Données de test
email = "moussa.diop@digit-hab.com"
password = "test123"

print("\n" + "="*60)
print("TEST DE LOGIN")
print("="*60 + "\n")

# 1. Vérifier que l'utilisateur existe
print("1. Recherche de l'utilisateur...")
try:
    user = User.objects.get(email=email)
    print(f"   ✅ Utilisateur trouvé: {user.username}")
    print(f"   - Email: {user.email}")
    print(f"   - Active: {user.is_active}")
except User.DoesNotExist:
    print(f"   ❌ Utilisateur avec email '{email}' non trouvé!")
    exit(1)

# 2. Vérifier le mot de passe
print("\n2. Vérification du mot de passe...")
if user.check_password(password):
    print(f"   ✅ Mot de passe correct!")
else:
    print(f"   ❌ Mot de passe incorrect!")
    exit(1)

# 3. Générer les tokens JWT
print("\n3. Génération des tokens JWT...")
try:
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    
    print(f"   ✅ Tokens générés avec succès!")
    print(f"\n   Refresh Token (premiers 50 caractères):")
    print(f"   {refresh_token[:50]}...")
    print(f"\n   Access Token (premiers 50 caractères):")
    print(f"   {access_token[:50]}...")
    
except Exception as e:
    print(f"   ❌ Erreur lors de la génération des tokens: {e}")
    exit(1)

# 4. Simuler la réponse de l'API
print("\n4. Réponse API simulée:")
print("-" * 60)
response = {
    'refresh': refresh_token,
    'access': access_token,
    'user': {
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role if hasattr(user, 'role') else 'client',
    }
}

import json
print(json.dumps(response, indent=2))

print("\n" + "="*60)
print("✅ TEST RÉUSSI!")
print("="*60 + "\n")

# 5. Test du serializer
print("5. Test du serializer...")
from apps.auth.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError

serializer_data = {
    'email': email,
    'password': password
}

serializer = TokenObtainPairSerializer(data=serializer_data)
if serializer.is_valid():
    print("   ✅ Serializer valide!")
    print(f"   Données validées: {list(serializer.validated_data.keys())}")
else:
    print("   ❌ Serializer invalide!")
    print(f"   Erreurs: {serializer.errors}")

print("\n" + "="*60)

