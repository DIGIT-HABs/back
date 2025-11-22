#!/usr/bin/env python
"""
Script pour créer des données de test pour DIGIT-HAB CRM
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from apps.auth.models import User, Agency
from apps.properties.models import Property

def create_test_data():
    """Créer des données de test complètes."""
    
    print("🚀 Création des données de test DIGIT-HAB...\n")
    
    # 1. Créer une agence
    print("1️⃣ Création de l'agence...")
    agency, created = Agency.objects.get_or_create(
        email="contact@digit-hab.com",
        defaults={
            'name': "Digit Hab Dakar",
            'legal_name': "Digit Hab Sénégal SARL",
            'phone': "+221771234567",
            'address_line1': "Rue 10, Almadies",
            'city': "Dakar",
            'postal_code': "12500",
            'country': "Sénégal",
            'vat_number': "SN123456789",
            'license_number': "AGE-2024-001",
            'subscription_type': "premium",
            'is_active': True,
            'is_trial': False,
            'subscription_start': datetime.now(),
            'subscription_end': datetime.now() + timedelta(days=365),
            'max_agents': 10,
            'max_properties': 500,
            'max_clients': 1000,
        }
    )
    if created:
        print(f"   ✅ Agence créée : {agency.name}")
    else:
        print(f"   ℹ️  Agence existante : {agency.name}")
    
    # 2. Créer des agents
    print("\n2️⃣ Création des agents...")
    agents_data = [
        {
            'username': 'agent1',
            'email': 'moussa.diop@digit-hab.com',
            'first_name': 'Moussa',
            'last_name': 'Diop',
            'phone': '+221771234567',
        },
        {
            'username': 'agent2',
            'email': 'fatou.sall@digit-hab.com',
            'first_name': 'Fatou',
            'last_name': 'Sall',
            'phone': '+221779876543',
        },
        {
            'username': 'agent3',
            'email': 'omar.ba@digit-hab.com',
            'first_name': 'Omar',
            'last_name': 'Ba',
            'phone': '+221775554444',
        },
    ]
    
    agents = []
    for agent_data in agents_data:
        agent, created = User.objects.get_or_create(
            username=agent_data['username'],
            defaults={
                **agent_data,
                'password': 'pbkdf2_sha256$600000$test$test',  # password: "test123"
                'is_active': True,
                'is_verified': True,
            }
        )
        if created:
            agent.set_password('test123')
            agent.save()
            print(f"   ✅ Agent créé : {agent.get_full_name()}")
        else:
            print(f"   ℹ️  Agent existant : {agent.get_full_name()}")
        agents.append(agent)
    
    # 3. Créer des propriétés
    print("\n3️⃣ Création des propriétés...")
    
    properties_data = [
        {
            'title': 'Villa Moderne Almadies',
            'description': 'Magnifique villa moderne avec piscine et jardin tropical. Vue imprenable sur l\'océan. Quartier calme et sécurisé des Almadies.',
            'property_type': 'villa',
            'status': 'available',
            'price': Decimal('250000000'),
            'city': 'Dakar',
            'address_line1': 'Almadies, Route de Ngor',
            'postal_code': '12500',
            'country': 'Sénégal',
            'surface_area': Decimal('350'),
            'rooms': 6,
            'bedrooms': 5,
            'bathrooms': 4,
            'has_parking': True,
            'has_garden': True,
            'has_pool': True,
            'has_elevator': False,
            'has_security_system': True,
            'has_air_conditioning': True,
            'energy_class': 'B',
            'is_featured': True,
        },
        {
            'title': 'Appartement Luxe Plateau',
            'description': 'Appartement moderne au cœur du Plateau. Proche de tous commerces et administrations. Idéal pour professionnels.',
            'property_type': 'apartment',
            'status': 'available',
            'price': Decimal('85000000'),
            'city': 'Dakar',
            'address_line1': 'Avenue Georges Pompidou, Plateau',
            'postal_code': '10000',
            'country': 'Sénégal',
            'surface_area': Decimal('125'),
            'rooms': 4,
            'bedrooms': 3,
            'bathrooms': 2,
            'has_parking': True,
            'has_garden': False,
            'has_pool': False,
            'has_elevator': True,
            'has_security_system': True,
            'has_air_conditioning': True,
            'energy_class': 'A',
            'is_featured': True,
        },
        {
            'title': 'Duplex Moderne Mermoz',
            'description': 'Splendide duplex dans résidence standing à Mermoz. Lumineux et spacieux avec terrasse panoramique.',
            'property_type': 'duplex',
            'status': 'available',
            'price': Decimal('120000000'),
            'city': 'Dakar',
            'address_line1': 'Mermoz Pyrotechnie',
            'postal_code': '11000',
            'country': 'Sénégal',
            'surface_area': Decimal('180'),
            'rooms': 5,
            'bedrooms': 4,
            'bathrooms': 3,
            'has_parking': True,
            'has_garden': False,
            'has_pool': True,
            'has_elevator': True,
            'has_security_system': True,
            'has_air_conditioning': True,
            'energy_class': 'B',
            'is_featured': True,
        },
        {
            'title': 'Villa Familiale Sacré-Cœur',
            'description': 'Grande villa familiale dans quartier résidentiel calme. Parfaite pour grande famille.',
            'property_type': 'house',
            'status': 'available',
            'price': Decimal('165000000'),
            'city': 'Dakar',
            'address_line1': 'Sacré-Cœur 3',
            'postal_code': '11500',
            'country': 'Sénégal',
            'surface_area': Decimal('280'),
            'rooms': 6,
            'bedrooms': 5,
            'bathrooms': 3,
            'has_parking': True,
            'has_garden': True,
            'has_pool': False,
            'has_elevator': False,
            'has_security_system': True,
            'has_air_conditioning': True,
            'energy_class': 'C',
            'is_featured': False,
        },
        {
            'title': 'Penthouse Vue Mer Mamelles',
            'description': 'Penthouse d\'exception avec vue panoramique sur l\'océan Atlantique. Luxe et raffinement.',
            'property_type': 'penthouse',
            'status': 'available',
            'price': Decimal('320000000'),
            'city': 'Dakar',
            'address_line1': 'Les Mamelles, Route de la Corniche',
            'postal_code': '13000',
            'country': 'Sénégal',
            'surface_area': Decimal('240'),
            'rooms': 5,
            'bedrooms': 4,
            'bathrooms': 3,
            'has_parking': True,
            'has_garden': False,
            'has_pool': True,
            'has_elevator': True,
            'has_security_system': True,
            'has_air_conditioning': True,
            'energy_class': 'A',
            'is_featured': True,
        },
        {
            'title': 'Studio Moderne Liberté 6',
            'description': 'Studio meublé tout confort. Idéal étudiant ou jeune professionnel.',
            'property_type': 'studio',
            'status': 'available',
            'price': Decimal('28000000'),
            'city': 'Dakar',
            'address_line1': 'Liberté 6 Extension',
            'postal_code': '14000',
            'country': 'Sénégal',
            'surface_area': Decimal('45'),
            'rooms': 1,
            'bedrooms': 1,
            'bathrooms': 1,
            'has_parking': True,
            'has_garden': False,
            'has_pool': False,
            'has_elevator': True,
            'has_security_system': True,
            'has_air_conditioning': True,
            'energy_class': 'B',
            'is_featured': False,
        },
        {
            'title': 'Appartement Famille Point E',
            'description': 'Bel appartement familial dans quartier animé de Point E. Proche écoles et commerces.',
            'property_type': 'apartment',
            'status': 'available',
            'price': Decimal('72000000'),
            'city': 'Dakar',
            'address_line1': 'Point E, Rue 6',
            'postal_code': '15000',
            'country': 'Sénégal',
            'surface_area': Decimal('110'),
            'rooms': 4,
            'bedrooms': 3,
            'bathrooms': 2,
            'has_parking': True,
            'has_garden': False,
            'has_pool': False,
            'has_elevator': True,
            'has_security_system': True,
            'has_air_conditioning': True,
            'energy_class': 'C',
            'is_featured': False,
        },
        {
            'title': 'Villa Prestige Fann Résidence',
            'description': 'Villa de prestige dans le quartier huppé de Fann Résidence. Architecture contemporaine.',
            'property_type': 'villa',
            'status': 'reserved',
            'price': Decimal('450000000'),
            'city': 'Dakar',
            'address_line1': 'Fann Résidence',
            'postal_code': '16000',
            'country': 'Sénégal',
            'surface_area': Decimal('500'),
            'rooms': 8,
            'bedrooms': 6,
            'bathrooms': 5,
            'has_parking': True,
            'has_garden': True,
            'has_pool': True,
            'has_elevator': True,
            'has_security_system': True,
            'has_air_conditioning': True,
            'energy_class': 'A',
            'is_featured': True,
        },
    ]
    
    for i, prop_data in enumerate(properties_data):
        # Alterner entre les agents
        agent = agents[i % len(agents)]
        
        # Calculer price_per_sqm
        price_per_sqm = prop_data['price'] / prop_data['surface_area']
        
        prop, created = Property.objects.get_or_create(
            title=prop_data['title'],
            defaults={
                **prop_data,
                'agent': agent,
                'agency': agency,
                'price_per_sqm': price_per_sqm,
            }
        )
        
        if created:
            print(f"   ✅ Propriété créée : {prop.title}")
            print(f"      💰 Prix : {prop.price:,.0f} FCFA")
            print(f"      📍 Ville : {prop.city}")
            print(f"      🏠 Type : {prop.get_property_type_display()}")
            print(f"      📊 Status : {prop.get_status_display()}")
        else:
            print(f"   ℹ️  Propriété existante : {prop.title}")
    
    # Statistiques finales
    print("\n" + "="*50)
    print("📊 STATISTIQUES")
    print("="*50)
    print(f"✅ Agences : {Agency.objects.count()}")
    print(f"✅ Agents : {User.objects.count()}")
    print(f"✅ Propriétés : {Property.objects.count()}")
    print(f"   - Disponibles : {Property.objects.filter(status='available').count()}")
    print(f"   - Featured : {Property.objects.filter(is_featured=True).count()}")
    print(f"   - Réservées : {Property.objects.filter(status='reserved').count()}")
    print("\n✨ Données de test créées avec succès !\n")
    
    print("📝 Connexion Admin:")
    print("   URL: http://localhost:8000/admin/")
    print("   Créer superuser: python manage.py createsuperuser")
    print("\n📝 Connexion Agent:")
    print("   Email: moussa.diop@digit-hab.com")
    print("   Password: test123")
    print("\n🚀 Lancer le serveur:")
    print("   python manage.py runserver")

if __name__ == '__main__':
    try:
        create_test_data()
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

