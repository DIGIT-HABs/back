import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from apps.auth.serializers import TokenObtainPairSerializer

print("\n🔍 Test rapide du serializer...\n")

serializer = TokenObtainPairSerializer(data={
    'email': 'moussa.diop@digit-hab.com',
    'password': 'test123'
})

if serializer.is_valid():
    print("✅ SUCCÈS!")
    print(f"✅ Access token disponible")
    print(f"✅ Refresh token disponible")
    print(f"✅ Données utilisateur disponibles")
else:
    print("❌ ÉCHEC!")
    print(f"Erreurs: {serializer.errors}")

