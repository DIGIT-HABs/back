"""
Script pour générer des données de test pour le CRM
Phase 1 - Post-deployment
"""

import os
import django
import sys
from datetime import datetime, timedelta
from random import choice, randint, uniform

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.crm.models import ClientProfile, ClientNote, ClientInteraction, PropertyInterest
from apps.auth.models import Agency
from apps.properties.models import Property

User = get_user_model()

def create_test_clients(num_clients=20):
    """Créer des clients de test"""
    
    print(f"🔄 Création de {num_clients} clients de test...")
    
    # Récupérer ou créer une agence
    try:
        agency = Agency.objects.first()
        if not agency:
            print("❌ Aucune agence trouvée. Créez d'abord une agence.")
            return
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    # Récupérer ou créer un agent
    try:
        agent = User.objects.filter(role='agent').first()
        if not agent:
            print("⚠️  Aucun agent trouvé. Création d'un agent de test...")
            agent = User.objects.create_user(
                username='agent_test',
                email='agent@test.com',
                password='password123',
                first_name='Agent',
                last_name='Test',
                role='agent',
                phone='+33612345678'
            )
            # Créer le profil de l'agent
            from apps.auth.models import UserProfile
            UserProfile.objects.get_or_create(
                user=agent,
                defaults={'agency': agency}
            )
            print(f"✅ Agent créé: {agent.username}")
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'agent: {e}")
        return
    
    # Prénoms et noms français
    first_names = [
        'Jean', 'Marie', 'Pierre', 'Sophie', 'Luc', 'Anne', 
        'Michel', 'Julie', 'Paul', 'Claire', 'Thomas', 'Emma',
        'Nicolas', 'Laura', 'David', 'Camille', 'Alexandre', 'Sarah'
    ]
    
    last_names = [
        'Dupont', 'Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert',
        'Richard', 'Petit', 'Durand', 'Leroy', 'Moreau', 'Simon',
        'Laurent', 'Lefebvre', 'Michel', 'Garcia', 'David', 'Bertrand'
    ]
    
    statuses = ['active', 'inactive', 'lead', 'converted']
    priorities = ['high', 'medium', 'low']
    property_types = ['apartment', 'house', 'villa', 'studio']
    locations = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Bordeaux']
    tags_options = [
        'vip', 'investisseur', 'premier_achat', 'urgence', 
        'famille', 'retraite', 'entreprise', 'relocation'
    ]
    
    clients_created = 0
    
    for i in range(num_clients):
        try:
            # Créer un utilisateur
            first_name = choice(first_names)
            last_name = choice(last_names)
            username = f"{first_name.lower()}_{last_name.lower()}_{i}"
            email = f"{first_name.lower()}.{last_name.lower()}{i}@test.com"
            
            # Vérifier si l'utilisateur existe déjà
            if User.objects.filter(email=email).exists():
                print(f"⏭️  {email} existe déjà, passage au suivant...")
                continue
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                first_name=first_name,
                last_name=last_name,
                role='client',
                phone=f'+336{randint(10000000, 99999999)}'
            )
            
            # Créer le UserProfile
            from apps.auth.models import UserProfile
            UserProfile.objects.get_or_create(
                user=user,
                defaults={'agency': agency}
            )
            
            # Créer le ClientProfile
            status = choice(statuses)
            priority = choice(priorities)
            min_budget = randint(100, 500) * 1000
            max_budget = min_budget + randint(100, 300) * 1000
            
            # Sélectionner 2-4 tags aléatoires
            num_tags = randint(2, 4)
            selected_tags = [choice(tags_options) for _ in range(num_tags)]
            
            client_profile = ClientProfile.objects.create(
                user=user,
                status=status,
                priority_level=priority,
                min_budget=min_budget,
                max_budget=max_budget,
                preferred_property_types=[choice(property_types) for _ in range(randint(1, 3))],
                preferred_locations=[choice(locations) for _ in range(randint(1, 3))],
                min_bedrooms=randint(1, 3),
                max_bedrooms=randint(2, 5),
                conversion_score=uniform(50, 95),
                total_properties_viewed=randint(0, 30),
                total_inquiries_made=randint(0, 15),
                tags=selected_tags,
                financing_status=choice(['approved', 'pending', 'not_started', 'rejected']),
                preferred_contact_method=choice(['email', 'phone', 'sms']),
            )
            
            # Créer 2-5 notes pour ce client
            num_notes = randint(2, 5)
            note_types = ['general', 'meeting', 'call', 'follow_up', 'alert', 'opportunity']
            
            for j in range(num_notes):
                is_important = choice([True, False, False, False])  # 25% de chance
                is_pinned = choice([True, False, False, False, False])  # 20% de chance
                
                ClientNote.objects.create(
                    client_profile=client_profile,
                    author=agent,
                    title=f"Note {j+1} - {choice(['Appel', 'Visite', 'Email', 'Suivi'])}",
                    content=f"Contenu de la note pour {user.get_full_name()}. Le client a montré de l'intérêt pour plusieurs propriétés.",
                    note_type=choice(note_types),
                    is_important=is_important,
                    is_pinned=is_pinned,
                    created_at=datetime.now() - timedelta(days=randint(0, 30))
                )
            
            # Créer 1-3 interactions
            num_interactions = randint(1, 3)
            interaction_types = ['call', 'email', 'meeting', 'visit', 'message']
            channels = ['phone', 'email', 'in_person', 'video_call', 'whatsapp']
            interaction_statuses = ['scheduled', 'completed', 'cancelled']
            outcomes = ['positive', 'negative', 'neutral', 'follow_up_needed']
            
            for k in range(num_interactions):
                scheduled_date = datetime.now() - timedelta(days=randint(1, 60))
                interaction_status = choice(interaction_statuses)
                
                ClientInteraction.objects.create(
                    client=user,
                    agent=agent,
                    interaction_type=choice(interaction_types),
                    channel=choice(channels),
                    subject=f"Interaction {k+1} avec {user.get_full_name()}",
                    content=f"Discussion concernant les préférences du client et les propriétés disponibles.",
                    status=interaction_status,
                    outcome=choice(outcomes) if interaction_status == 'completed' else None,
                    scheduled_date=scheduled_date,
                    completed_date=scheduled_date + timedelta(hours=1) if interaction_status == 'completed' else None,
                    duration_minutes=randint(15, 120) if interaction_status == 'completed' else None,
                    priority=choice(['low', 'medium', 'high']),
                    requires_follow_up=choice([True, False])
                )
            
            clients_created += 1
            print(f"✅ Client {clients_created}/{num_clients}: {user.get_full_name()} ({email})")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création du client {i+1}: {e}")
            continue
    
    print(f"\n🎉 Terminé! {clients_created} clients créés avec succès!")
    print(f"\n📊 Résumé:")
    print(f"   - {ClientProfile.objects.count()} profils clients")
    print(f"   - {ClientNote.objects.count()} notes")
    print(f"   - {ClientInteraction.objects.count()} interactions")


def show_stats():
    """Afficher les statistiques"""
    print("\n📊 STATISTIQUES CRM")
    print("=" * 50)
    print(f"Clients:       {ClientProfile.objects.count()}")
    print(f"Notes:         {ClientNote.objects.count()}")
    print(f"Interactions:  {ClientInteraction.objects.count()}")
    print(f"Agents:        {User.objects.filter(role='agent').count()}")
    print("=" * 50)


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🚀 GÉNÉRATION DE DONNÉES DE TEST CRM")
    print("=" * 50 + "\n")
    
    # Afficher les stats actuelles
    show_stats()
    
    # Demander confirmation
    print("\n⚠️  Voulez-vous créer des clients de test?")
    print("   Tapez le nombre de clients à créer (ex: 20)")
    print("   ou 'exit' pour quitter\n")
    
    if len(sys.argv) > 1:
        try:
            num = int(sys.argv[1])
            create_test_clients(num)
        except ValueError:
            print("❌ Nombre invalide")
    else:
        user_input = input("Nombre de clients: ").strip()
        
        if user_input.lower() == 'exit':
            print("👋 Au revoir!")
            sys.exit(0)
        
        try:
            num = int(user_input)
            if num > 0 and num <= 100:
                create_test_clients(num)
            else:
                print("❌ Choisissez un nombre entre 1 et 100")
        except ValueError:
            print("❌ Entrée invalide")
    
    # Afficher les stats finales
    show_stats()
