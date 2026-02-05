"""
Script simple pour créer des clients de test
Exécuter: python create_clients.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.crm.models import ClientProfile, ClientNote
from apps.auth.models import Agency, UserProfile

User = get_user_model()

print("\n" + "="*60)
print("🚀 CRÉATION DE CLIENTS DE TEST")
print("="*60 + "\n")

# Récupérer ou créer une agence
try:
    agency = Agency.objects.first()
    if not agency:
        print("⚠️  Création d'une agence de test...")
        agency = Agency.objects.create(
            name="Agence DIGIT-HAB",
            email="contact@digit-hab.com",
            phone="+33123456789",
            address="123 Avenue des Champs-Élysées, Paris"
        )
        print(f"✅ Agence créée: {agency.name}")
    else:
        print(f"✅ Agence trouvée: {agency.name}")
except Exception as e:
    print(f"❌ Erreur agence: {e}")
    exit(1)

# Récupérer ou créer un agent
try:
    agent = User.objects.filter(role='agent').first()
    if not agent:
        print("\n⚠️  Création d'un agent de test...")
        agent = User.objects.create_user(
            username='agent_demo',
            email='agent@digit-hab.com',
            password='demo123',
            first_name='Agent',
            last_name='Demo',
            role='agent',
            phone='+33612345678'
        )
        UserProfile.objects.get_or_create(
            user=agent,
            defaults={'agency': agency}
        )
        print(f"✅ Agent créé: {agent.username}")
        print(f"   📧 Email: {agent.email}")
        print(f"   🔑 Password: demo123")
    else:
        print(f"✅ Agent trouvé: {agent.username}")
except Exception as e:
    print(f"❌ Erreur agent: {e}")
    exit(1)

# Liste de clients à créer
clients_data = [
    {
        'username': 'jean.dupont',
        'email': 'jean.dupont@test.com',
        'first_name': 'Jean',
        'last_name': 'Dupont',
        'phone': '+33612345678',
        'status': 'active',
        'priority': 'high',
        'min_budget': 300000,
        'max_budget': 500000,
        'tags': ['vip', 'investisseur', 'urgent'],
        'property_types': ['apartment', 'house'],
        'locations': ['Paris', 'Neuilly-sur-Seine'],
        'note': 'Client très intéressé, budget élevé. Recherche activement.'
    },
    {
        'username': 'marie.martin',
        'email': 'marie.martin@test.com',
        'first_name': 'Marie',
        'last_name': 'Martin',
        'phone': '+33687654321',
        'status': 'active',
        'priority': 'medium',
        'min_budget': 200000,
        'max_budget': 350000,
        'tags': ['famille', 'premier_achat'],
        'property_types': ['house'],
        'locations': ['Lyon', 'Villeurbanne'],
        'note': 'Famille avec 2 enfants. Recherche une maison avec jardin.'
    },
    {
        'username': 'pierre.bernard',
        'email': 'pierre.bernard@test.com',
        'first_name': 'Pierre',
        'last_name': 'Bernard',
        'phone': '+33698765432',
        'status': 'lead',
        'priority': 'low',
        'min_budget': 150000,
        'max_budget': 250000,
        'tags': ['jeune', 'premier_achat'],
        'property_types': ['apartment'],
        'locations': ['Marseille'],
        'note': 'Jeune actif, premier achat. À qualifier.'
    },
    {
        'username': 'sophie.dubois',
        'email': 'sophie.dubois@test.com',
        'first_name': 'Sophie',
        'last_name': 'Dubois',
        'phone': '+33623456789',
        'status': 'active',
        'priority': 'high',
        'min_budget': 400000,
        'max_budget': 600000,
        'tags': ['vip', 'retraite', 'relocation'],
        'property_types': ['villa', 'house'],
        'locations': ['Nice', 'Cannes', 'Antibes'],
        'note': 'Retraitée, budget important. Recherche villa en bord de mer.'
    },
    {
        'username': 'luc.moreau',
        'email': 'luc.moreau@test.com',
        'first_name': 'Luc',
        'last_name': 'Moreau',
        'phone': '+33634567890',
        'status': 'converted',
        'priority': 'medium',
        'min_budget': 250000,
        'max_budget': 350000,
        'tags': ['investisseur', 'entreprise'],
        'property_types': ['apartment'],
        'locations': ['Bordeaux'],
        'note': 'Client converti. A acheté un appartement.'
    },
]

print("\n" + "="*60)
print("📝 CRÉATION DES CLIENTS")
print("="*60 + "\n")

created_count = 0

for data in clients_data:
    try:
        # Vérifier si le client existe déjà
        if User.objects.filter(email=data['email']).exists():
            print(f"⏭️  {data['first_name']} {data['last_name']} existe déjà")
            continue
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password='demo123',
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='client',
            phone=data['phone']
        )
        
        # Créer ou récupérer le UserProfile
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'agency': agency}
        )
        
        # Créer le ClientProfile
        client_profile = ClientProfile.objects.create(
            user=user,
            status=data['status'],
            priority_level=data['priority'],
            min_budget=data['min_budget'],
            max_budget=data['max_budget'],
            tags=data['tags'],
            preferred_property_types=data['property_types'],
            preferred_locations=data['locations'],
            min_bedrooms=2,
            max_bedrooms=4,
            conversion_score=75.0 if data['status'] == 'active' else 50.0,
            financing_status='approved' if data['priority'] == 'high' else 'pending',
            preferred_contact_method='email'
        )
        
        # Créer une note
        ClientNote.objects.create(
            client_profile=client_profile,
            author=agent,
            title="Premier contact",
            content=data['note'],
            note_type='general',
            is_important=data['priority'] == 'high',
            is_pinned=data['status'] == 'active' and data['priority'] == 'high'
        )
        
        created_count += 1
        
        # Afficher les infos
        print(f"✅ {data['first_name']} {data['last_name']}")
        print(f"   📧 {data['email']}")
        print(f"   🔑 Password: demo123")
        print(f"   💰 Budget: {data['min_budget']:,}€ - {data['max_budget']:,}€")
        print(f"   🏷️  Tags: {', '.join(data['tags'])}")
        print(f"   📍 {', '.join(data['locations'])}")
        print()
        
    except Exception as e:
        print(f"❌ Erreur pour {data['first_name']} {data['last_name']}: {e}\n")
        continue

print("="*60)
print("📊 RÉSUMÉ")
print("="*60)
print(f"✅ {created_count} nouveaux clients créés")
print(f"📝 Total clients: {ClientProfile.objects.count()}")
print(f"📝 Total notes: {ClientNote.objects.count()}")
print(f"👥 Total agents: {User.objects.filter(role='agent').count()}")
print("="*60)

print("\n🎯 POUR TESTER:")
print("   1. Démarrer le serveur: python manage.py runserver")
print("   2. Tester l'API: http://localhost:8000/api/crm/clients/")
print("   3. Admin Django: http://localhost:8000/admin/")
print("      - Username: agent_demo")
print("      - Password: demo123")
print("\n✨ C'est prêt !\n")
