"""
Script pour créer des données de test pour le module Calendar
"""

import os
import django
from datetime import datetime, date, time, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.db import transaction
from apps.calendar.models import (
    WorkingHours, TimeSlot, ClientAvailability, VisitSchedule,
    SchedulingPreference, ScheduleMetrics
)
from apps.properties.models import Property
from apps.reservations.models import Reservation
from apps.crm.models import ClientProfile

User = get_user_model()

def print_success(msg):
    print(f"✓ {msg}")

def print_error(msg):
    print(f"✗ {msg}")

def print_info(msg):
    print(f"ℹ {msg}")

@transaction.atomic
def create_test_data():
    """Crée des données de test complètes"""
    
    print("\n" + "="*60)
    print("🧪 CRÉATION DES DONNÉES DE TEST CALENDAR")
    print("="*60 + "\n")
    
    # Désactiver temporairement les signaux pour éviter les erreurs
    from apps.crm import signals as crm_signals
    post_save.disconnect(crm_signals.client_profile_post_save, sender=ClientProfile)
    print_info("Signaux CRM temporairement désactivés pour la création")
    
    # ========================================================================
    # 1. Récupérer/Créer des utilisateurs
    # ========================================================================
    print_info("Récupération des utilisateurs...")
    
    # Agents
    agent1 = User.objects.filter(email="fatou.sall@digit-hab.com").first()
    agent2 = User.objects.filter(email="mamadou.diop@digit-hab.com").first()
    
    # Clients
    client1 = User.objects.filter(email="client1@test.com").first()
    if not client1:
        client1 = User.objects.create_user(
            username='client1',
            email='client1@test.com',
            password='test123',
            first_name='Jean',
            last_name='Dupont'
        )
        print_success("Client 1 créé")
    
    client2 = User.objects.filter(email="client2@test.com").first()
    if not client2:
        client2 = User.objects.create_user(
            username='client2',
            email='client2@test.com',
            password='test123',
            first_name='Marie',
            last_name='Martin'
        )
        print_success("Client 2 créé")
    
    if not agent1:
        print_error("Agent 1 (Fatou) non trouvé")
        return
    
    print_success(f"Agent 1: {agent1.get_full_name()}")
    print_success(f"Client 1: {client1.get_full_name()}")
    print_success(f"Client 2: {client2.get_full_name()}")
    
    # ========================================================================
    # 2. Créer des Working Hours pour l'agent
    # ========================================================================
    print_info("\nCréation des horaires de travail...")
    
    # Supprimer les anciens
    WorkingHours.objects.filter(user=agent1).delete()
    
    # Créer horaires pour la semaine (Lundi-Vendredi)
    for day in range(5):  # 0-4 = Lundi-Vendredi
        WorkingHours.objects.create(
            user=agent1,
            day_of_week=day,
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_working=True,
            break_start=time(12, 0),
            break_end=time(13, 0)
        )
    
    # Samedi (demi-journée)
    WorkingHours.objects.create(
        user=agent1,
        day_of_week=5,
        start_time=time(9, 0),
        end_time=time(13, 0),
        is_working=True
    )
    
    # Dimanche (repos) - Mettre des horaires même si is_working=False
    WorkingHours.objects.create(
        user=agent1,
        day_of_week=6,
        start_time=time(9, 0),
        end_time=time(17, 0),
        is_working=False
    )
    
    print_success(f"7 horaires créés pour {agent1.get_full_name()}")
    
    # ========================================================================
    # 3. Créer des Time Slots
    # ========================================================================
    print_info("\nCréation des créneaux horaires...")
    
    # Supprimer les anciens
    TimeSlot.objects.filter(user=agent1).delete()
    
    # Créer créneaux pour les 7 prochains jours
    today = date.today()
    slots_created = 0
    
    for i in range(7):
        current_date = today + timedelta(days=i)
        day_of_week = current_date.weekday()  # 0 = Lundi
        
        # Trouver les horaires de travail
        working_hours = WorkingHours.objects.filter(
            user=agent1,
            day_of_week=day_of_week,
            is_working=True
        ).first()
        
        if working_hours:
            # Créer 4 créneaux de 2h chacun
            current_time = working_hours.start_time
            
            for slot_num in range(4):
                # Calculer fin du créneau
                end_datetime = datetime.combine(date.today(), current_time) + timedelta(hours=2)
                end_time = end_datetime.time()
                
                # Ne pas dépasser l'heure de fin
                if end_time <= working_hours.end_time:
                    # Skip la pause déjeuner
                    if not (working_hours.break_start and 
                           working_hours.break_start <= current_time < working_hours.break_end):
                        TimeSlot.objects.create(
                            user=agent1,
                            date=current_date,
                            start_time=current_time,
                            end_time=end_time,
                            status='available'
                        )
                        slots_created += 1
                
                # Passer au prochain créneau
                current_time = end_time
    
    print_success(f"{slots_created} créneaux créés pour les 7 prochains jours")
    
    # ========================================================================
    # 4. Créer des Client Availabilities
    # ========================================================================
    print_info("\nCréation des disponibilités clients...")
    
    # Supprimer les anciennes
    ClientAvailability.objects.filter(user__in=[client1, client2]).delete()
    
    # Client 1 - Disponibilité matin
    ClientAvailability.objects.create(
        user=client1,
        preferred_date=today + timedelta(days=2),
        preferred_time_slot='morning',
        urgency='high',
        preferred_duration=60,
        notes="Préfère le matin avant 11h"
    )
    
    # Client 2 - Disponibilité après-midi
    ClientAvailability.objects.create(
        user=client2,
        preferred_date=today + timedelta(days=3),
        preferred_time_slot='afternoon',
        urgency='normal',
        preferred_duration=90,
        notes="Disponible tout l'après-midi"
    )
    
    print_success("2 disponibilités clients créées")
    
    # ========================================================================
    # 5. Créer des Réservations et Planifications
    # ========================================================================
    print_info("\nCréation des réservations et planifications...")
    
    # Récupérer des propriétés
    properties = Property.objects.filter(is_public=True)[:3]
    
    if properties.count() < 3:
        print_error("Pas assez de propriétés disponibles (besoin de 3)")
        return
    
    schedules_created = 0
    
    # Créer ou récupérer les ClientProfile
    client_profile1, _ = ClientProfile.objects.get_or_create(
        user=client1,
        defaults={
            'status': 'active',
            'priority_level': 'high'
        }
    )
    
    client_profile2, _ = ClientProfile.objects.get_or_create(
        user=client2,
        defaults={
            'status': 'active',
            'priority_level': 'medium'
        }
    )
    
    print_success("Profils clients créés/récupérés")
    
    # Planification 1 - Aujourd'hui
    try:
        reservation1 = Reservation.objects.filter(
            client_profile=client_profile1,
            property=properties[0]
        ).first()
        
        if not reservation1:
            reservation1 = Reservation.objects.create(
                property=properties[0],
                client_profile=client_profile1,
                client_name=client1.get_full_name(),
                client_email=client1.email,
                scheduled_date=datetime.combine(today, time(10, 0)),
                status='pending',
                reservation_type='visit',
                assigned_agent=agent1
            )
        
        # Vérifier si pas déjà de schedule
        if not hasattr(reservation1, 'schedule'):
            VisitSchedule.objects.create(
                client=client1,
                agent=agent1,
                property=properties[0],
                reservation=reservation1,
                scheduled_date=today,
                scheduled_start_time=time(10, 0),
                scheduled_end_time=time(11, 0),
                status='confirmed',
                priority='high',
                match_score=0.95,
                match_factors={'date_match': 1.0, 'time_match': 0.9}
            )
            schedules_created += 1
            print_success("Planification 1 créée (Aujourd'hui - Confirmée)")
    except Exception as e:
        print_error(f"Erreur création planification 1: {e}")
    
    # Planification 2 - Demain
    try:
        tomorrow = today + timedelta(days=1)
        reservation2 = Reservation.objects.filter(
            client_profile=client_profile2,
            property=properties[1]
        ).first()
        
        if not reservation2:
            reservation2 = Reservation.objects.create(
                property=properties[1],
                client_profile=client_profile2,
                client_name=client2.get_full_name(),
                client_email=client2.email,
                scheduled_date=datetime.combine(tomorrow, time(14, 0)),
                status='pending',
                reservation_type='visit',
                assigned_agent=agent1
            )
        
        if not hasattr(reservation2, 'schedule'):
            VisitSchedule.objects.create(
                client=client2,
                agent=agent1,
                property=properties[1],
                reservation=reservation2,
                scheduled_date=tomorrow,
                scheduled_start_time=time(14, 0),
                scheduled_end_time=time(15, 30),
                status='scheduled',
                priority='normal',
                match_score=0.85
            )
            schedules_created += 1
            print_success("Planification 2 créée (Demain - Planifiée)")
    except Exception as e:
        print_error(f"Erreur création planification 2: {e}")
    
    # Planification 3 - Dans 3 jours
    try:
        future_date = today + timedelta(days=3)
        reservation3 = Reservation.objects.filter(
            client_profile=client_profile1,
            property=properties[2]
        ).first()
        
        if not reservation3:
            reservation3 = Reservation.objects.create(
                property=properties[2],
                client_profile=client_profile1,
                client_name=client1.get_full_name(),
                client_email=client1.email,
                scheduled_date=datetime.combine(future_date, time(11, 0)),
                status='pending',
                reservation_type='visit',
                assigned_agent=agent1
            )
        
        if not hasattr(reservation3, 'schedule'):
            VisitSchedule.objects.create(
                client=client1,
                agent=agent1,
                property=properties[2],
                reservation=reservation3,
                scheduled_date=future_date,
                scheduled_start_time=time(11, 0),
                scheduled_end_time=time(12, 0),
                status='pending',
                priority='urgent',
                match_score=0.78
            )
            schedules_created += 1
            print_success("Planification 3 créée (Dans 3 jours - En attente)")
    except Exception as e:
        print_error(f"Erreur création planification 3: {e}")
    
    print_success(f"{schedules_created} planifications créées")
    
    # ========================================================================
    # 6. Créer des Préférences
    # ========================================================================
    print_info("\nCréation des préférences de planification...")
    
    pref, created = SchedulingPreference.objects.get_or_create(
        user=agent1,
        defaults={
            'route_optimization': 'time',
            'client_preference_handling': 'prioritize',
            'max_daily_visits': 6,
            'min_break_minutes': 30,
            'travel_time_buffer': 15,
            'working_radius': 30.0,
            'preferred_areas': ['Dakar', 'Pikine', 'Guédiawaye'],
            'preferred_property_types': ['apartment', 'house']
        }
    )
    
    if created:
        print_success("Préférences créées pour l'agent")
    else:
        print_info("Préférences déjà existantes")
    
    # ========================================================================
    # RÉSUMÉ
    # ========================================================================
    print("\n" + "="*60)
    print("✅ DONNÉES DE TEST CRÉÉES")
    print("="*60)
    
    print(f"\n📊 Résumé:")
    print(f"  - Horaires de travail: {WorkingHours.objects.filter(user=agent1).count()}")
    print(f"  - Créneaux disponibles: {TimeSlot.objects.filter(user=agent1, status='available').count()}")
    print(f"  - Disponibilités clients: {ClientAvailability.objects.count()}")
    print(f"  - Planifications: {VisitSchedule.objects.count()}")
    print(f"  - Préférences: {SchedulingPreference.objects.count()}")
    
    print("\n🎯 Vous pouvez maintenant tester les endpoints Calendar !")
    print("   Lancez: python test_calendar_endpoints.py\n")
    
    # Réactiver les signaux
    post_save.connect(crm_signals.client_profile_post_save, sender=ClientProfile)
    print_info("Signaux CRM réactivés")

if __name__ == "__main__":
    try:
        create_test_data()
    except Exception as e:
        print_error(f"Erreur générale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Réactiver les signaux en cas d'erreur
        try:
            from apps.crm import signals as crm_signals
            post_save.connect(crm_signals.client_profile_post_save, sender=ClientProfile)
        except:
            pass

