"""
Script simplifié pour créer des données de test
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings.prod')
django.setup()

from apps.auth.models import User, Agency, UserProfile
from apps.properties.models import Property
from apps.crm.models import ClientProfile
from django.utils import timezone
from datetime import timedelta

print("=" * 60)
print("🚀 Création des Données de Test")
print("=" * 60)
print("")

# ════════════════════════════════════════════════════════
# 1. Agence
# ════════════════════════════════════════════════════════

print("🏢 Agence...")
agency, _ = Agency.objects.get_or_create(
    name='DIGIT-HAB Immobilier',
    defaults={
        'license_number': 'DH-2026-001',
        'email': 'contact@digit-hab.com',
        'phone': '+221338234567',
        'address_line1': '123 Avenue Cheikh Anta Diop',
        'city': 'Dakar',
        'postal_code': '10000',
        'subscription_type': 'premium',
        'subscription_start': timezone.now(),
        'subscription_end': timezone.now() + timedelta(days=365),
    }
)
print(f"✅ {agency.name}")

# ════════════════════════════════════════════════════════
# 2. Agents
# ════════════════════════════════════════════════════════

print("")
print("👥 Agents...")
agents = []
for i, data in enumerate([
    ('agent1', 'Moussa', 'Diop', 'moussa.diop@digit-hab.com'),
    ('agent2', 'Fatou', 'Sall', 'fatou.sall@digit-hab.com'),
], 1):
    user, created = User.objects.get_or_create(
        username=data[0],
        defaults={
            'email': data[3],
            'first_name': data[1],
            'last_name': data[2],
            'role': 'agent',
            'is_verified': True,
        }
    )
    if created:
        user.set_password('password123')
        user.save()
    
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={'agency': agency}
    )
    agents.append(user)
    print(f"✅ {user.get_full_name()}")

# ════════════════════════════════════════════════════════
# 3. Propriétés
# ════════════════════════════════════════════════════════

print("")
print("🏠 Propriétés...")
properties = [
    {
        'title': 'Appartement F4 Almadies',
        'property_type': 'apartment',
        'property_type_display': 'sale',
        'price': 85000000,
        'surface_area': 120,
        'rooms': 4,
        'bedrooms': 4,
        'bathrooms': 2,
        'address_line1': 'Almadies',
        'city': 'Dakar',
        'postal_code': '10000',
        'description': 'Bel appartement vue mer',
    },
    {
        'title': 'Villa R+2 Saly',
        'property_type': 'villa',
        'property_type_display': 'sale',
        'price': 150000000,
        'surface_area': 350,
        'rooms': 8,
        'bedrooms': 6,
        'bathrooms': 4,
        'address_line1': 'Saly',
        'city': 'Mbour',
        'postal_code': '20000',
        'description': 'Villa avec piscine',
    },
    {
        'title': 'Studio Plateau',
        'property_type': 'studio',
        'property_type_display': 'rent',
        'price': 250000,
        'surface_area': 35,
        'rooms': 1,
        'bedrooms': 1,
        'bathrooms': 1,
        'address_line1': 'Plateau',
        'city': 'Dakar',
        'postal_code': '11000',
        'description': 'Studio meublé',
    },
]

for prop_data in properties:
    prop, created = Property.objects.get_or_create(
        title=prop_data['title'],
        defaults={
            **prop_data,
            'agency': agency,
            'agent': agents[0],
            'status': 'available',
            'is_featured': True,
            'is_public': True,
        }
    )
    if created:
        print(f"✅ {prop.title}")

# ════════════════════════════════════════════════════════
# RÉSUMÉ
# ════════════════════════════════════════════════════════

print("")
print("=" * 60)
print("📊 RÉSUMÉ")
print("=" * 60)
print(f"Agences:     {Agency.objects.count()}")
print(f"Agents:      {User.objects.filter(role='agent').count()}")
print(f"Propriétés:  {Property.objects.count()}")
print(f"Clients:     {ClientProfile.objects.count()}")
print("=" * 60)
print("")
print("✅ Données de test créées !")
print("")
print("🔐 Identifiants:")
print("   Username: agent1")
print("   Password: password123")
print("")
