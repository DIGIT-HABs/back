"""
Script pour créer des données de test en production
À exécuter sur le serveur VPS
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings.prod')
django.setup()

from apps.auth.models import User, Agency, UserProfile
from apps.properties.models import PropertyCategory, Property
from apps.crm.models import ClientProfile
from django.utils import timezone
from datetime import timedelta

print("=" * 60)
print("🚀 Création des Données de Test - DIGIT-HAB CRM")
print("=" * 60)
print("")

# ════════════════════════════════════════════════════════
# 1. Créer une Agence
# ════════════════════════════════════════════════════════

print("🏢 Création de l'agence...")

agency, created = Agency.objects.get_or_create(
    name='DIGIT-HAB Immobilier',
    defaults={
        'license_number': 'DH-2026-001',
        'email': 'contact@digit-hab.com',
        'phone': '+221338234567',
        'address_line1': '123 Avenue Cheikh Anta Diop',
        'city': 'Dakar',
        'postal_code': '10000',
        'country': 'Sénégal',
        'subscription_type': 'premium',
        'subscription_start': timezone.now(),
        'subscription_end': timezone.now() + timedelta(days=365),
        'max_agents': 50,
        'max_properties': 1000,
        'max_clients': 5000,
        'is_active': True,
    }
)

if created:
    print(f"✅ Agence créée: {agency.name}")
else:
    print(f"ℹ️  Agence existe: {agency.name}")

# ════════════════════════════════════════════════════════
# 2. Créer des Agents
# ════════════════════════════════════════════════════════

print("")
print("👥 Création des agents...")

agents_data = [
    {'username': 'agent1', 'email': 'moussa.diop@digit-hab.com', 'first_name': 'Moussa', 'last_name': 'Diop'},
    {'username': 'agent2', 'email': 'fatou.sall@digit-hab.com', 'first_name': 'Fatou', 'last_name': 'Sall'},
    {'username': 'agent3', 'email': 'ibrahima.ndiaye@digit-hab.com', 'first_name': 'Ibrahima', 'last_name': 'Ndiaye'},
]

agents = []
for agent_data in agents_data:
    user, created = User.objects.get_or_create(
        username=agent_data['username'],
        defaults={
            'email': agent_data['email'],
            'first_name': agent_data['first_name'],
            'last_name': agent_data['last_name'],
            'role': 'agent',
            'is_active': True,
            'is_verified': True,
        }
    )
    
    if created:
        user.set_password('password123')
        user.save()
        print(f"✅ Agent créé: {user.get_full_name()} ({user.username})")
    else:
        print(f"ℹ️  Agent existe: {user.get_full_name()} ({user.username})")
    
    # Créer/récupérer le profil
    profile, prof_created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'agency': agency,
            'position': 'Agent Commercial',
            'department': 'Ventes',
        }
    )
    
    if prof_created:
        print(f"   ✅ Profil créé pour {user.username}")
    
    agents.append(user)

# ════════════════════════════════════════════════════════
# 3. Créer des Catégories de Propriétés
# ════════════════════════════════════════════════════════

print("")
print("🏘️  Création des catégories...")

categories_data = [
    {'name': 'Appartement', 'code': 'APT', 'description': 'Appartements résidentiels'},
    {'name': 'Maison', 'code': 'HSE', 'description': 'Maisons individuelles'},
    {'name': 'Villa', 'code': 'VIL', 'description': 'Villas de luxe'},
    {'name': 'Studio', 'code': 'STD', 'description': 'Studios'},
    {'name': 'Bureau', 'code': 'OFF', 'description': 'Bureaux professionnels'},
    {'name': 'Commerce', 'code': 'COM', 'description': 'Locaux commerciaux'},
    {'name': 'Terrain', 'code': 'LND', 'description': 'Terrains à bâtir'},
]

categories = []
for cat_data in categories_data:
    cat, created = PropertyCategory.objects.get_or_create(
        code=cat_data['code'],
        defaults={
            'name': cat_data['name'],
            'description': cat_data['description'],
            'is_active': True,
            'display_order': len(categories) + 1,
        }
    )
    
    if created:
        print(f"✅ Catégorie créée: {cat.name}")
    else:
        print(f"ℹ️  Catégorie existe: {cat.name}")
    
    categories.append(cat)

# ════════════════════════════════════════════════════════
# 4. Créer des Propriétés
# ════════════════════════════════════════════════════════

print("")
print("🏠 Création des propriétés...")

properties_data = [
    {
        'title': 'Appartement F4 à Almadies',
        'category': categories[0],  # Appartement
        'property_type': 'sale',
        'price': 85000000,
        'surface_area': 120,
        'bedrooms': 4,
        'bathrooms': 2,
        'address': 'Almadies, Dakar',
        'city': 'Dakar',
        'description': 'Bel appartement neuf avec vue mer',
    },
    {
        'title': 'Villa R+2 à Saly',
        'category': categories[2],  # Villa
        'property_type': 'sale',
        'price': 150000000,
        'surface_area': 350,
        'bedrooms': 6,
        'bathrooms': 4,
        'address': 'Saly, Mbour',
        'city': 'Mbour',
        'description': 'Villa de luxe avec piscine',
    },
    {
        'title': 'Studio meublé Plateau',
        'category': categories[3],  # Studio
        'property_type': 'rent',
        'price': 250000,
        'surface_area': 35,
        'bedrooms': 1,
        'bathrooms': 1,
        'address': 'Plateau, Dakar',
        'city': 'Dakar',
        'description': 'Studio tout équipé, proche des commodités',
    },
]

for prop_data in properties_data:
    prop, created = Property.objects.get_or_create(
        title=prop_data['title'],
        defaults={
            **prop_data,
            'agency': agency,
            'created_by': agents[0],
            'status': 'available',
            'is_active': True,
            'is_featured': True,
        }
    )
    
    if created:
        print(f"✅ Propriété créée: {prop.title}")
    else:
        print(f"ℹ️  Propriété existe: {prop.title}")

# ════════════════════════════════════════════════════════
# RÉSUMÉ
# ════════════════════════════════════════════════════════

print("")
print("=" * 60)
print("📊 RÉSUMÉ DES DONNÉES CRÉÉES")
print("=" * 60)
print(f"Agences: {Agency.objects.count()}")
print(f"Agents: {User.objects.filter(role='agent').count()}")
print(f"Catégories: {PropertyCategory.objects.count()}")
print(f"Propriétés: {Property.objects.count()}")
print(f"Clients: {ClientProfile.objects.count()}")
print("=" * 60)
print("")
print("✅ Données de test créées avec succès !")
print("")
print("🔐 Identifiants de test:")
print("   Username: agent1")
print("   Password: password123")
print("")
