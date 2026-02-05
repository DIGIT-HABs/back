"""
Script de test pour les endpoints Calendar
Teste tous les endpoints de l'API Calendar
"""

import requests
import json
from datetime import datetime, timedelta, date, time

# Configuration
BASE_URL = "https://api.digit-hab.altoppe.sn/api/calendar"
AUTH_URL = "https://api.digit-hab.altoppe.sn/api/auth/login/"

# Couleurs pour le terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

# Session avec authentification
session = requests.Session()
token = None

def login():
    """Se connecter et obtenir le token"""
    global token
    
    print_info("Connexion à l'API...")
    
    # Essayer avec un utilisateur existant
    credentials = {
        "email": "fatou.sall@digit-hab.com",
        "password": "test123"
    }
    
    try:
        response = requests.post(AUTH_URL, json=credentials)
        if response.status_code == 200:
            data = response.json()
            token = data.get('access') or data.get('token')
            if token:
                session.headers.update({'Authorization': f'Bearer {token}'})
                print_success(f"Connecté avec succès")
                return True
    except Exception as e:
        print_error(f"Erreur connexion: {e}")
    
    print_warning("Tentative en mode public (sans auth)")
    return False

def test_endpoint(method, url, description, data=None, params=None, expect_auth=True):
    """Teste un endpoint"""
    print(f"\n{'='*60}")
    print_info(f"Test: {description}")
    print(f"URL: {url}")
    
    try:
        if method == 'GET':
            response = session.get(url, params=params)
        elif method == 'POST':
            response = session.post(url, json=data)
        elif method == 'PATCH':
            response = session.patch(url, json=data)
        elif method == 'DELETE':
            response = session.delete(url)
        else:
            print_error(f"Méthode {method} non supportée")
            return None
        
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print_success(f"Succès - {response.status_code}")
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
                return data
            except:
                print(f"Response (non-JSON): {response.text[:200]}")
                return response.text
        elif response.status_code == 403:
            print_warning(f"Forbidden - Vérifier les permissions")
            print(f"Response: {response.text[:200]}")
        elif response.status_code == 404:
            print_warning(f"Not Found - Endpoint ou ressource inexistante")
            print(f"Response: {response.text[:200]}")
        else:
            print_error(f"Erreur {response.status_code}")
            print(f"Response: {response.text[:200]}")
        
        return None
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return None

def main():
    """Tests principaux"""
    print("\n" + "="*60)
    print("🧪 TESTS DES ENDPOINTS CALENDAR API")
    print("="*60)
    
    # Login
    is_authenticated = login()
    
    # ========================================================================
    # 1. WORKING HOURS
    # ========================================================================
    print("\n" + "🕐"*30)
    print("WORKING HOURS (Horaires de travail)")
    print("🕐"*30)
    
    # GET working hours
    test_endpoint(
        'GET',
        f'{BASE_URL}/working-hours/',
        'Liste des horaires de travail'
    )
    
    # GET my hours
    if is_authenticated:
        test_endpoint(
            'GET',
            f'{BASE_URL}/working-hours/my_hours/',
            'Mes horaires de travail'
        )
    
    # POST create working hours
    if is_authenticated:
        test_endpoint(
            'POST',
            f'{BASE_URL}/working-hours/',
            'Créer des horaires',
            data={
                "day_of_week": 0,  # Lundi
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "is_working": True,
                "break_start": "12:00:00",
                "break_end": "13:00:00"
            }
        )
    
    # ========================================================================
    # 2. TIME SLOTS
    # ========================================================================
    print("\n" + "📅"*30)
    print("TIME SLOTS (Créneaux horaires)")
    print("📅"*30)
    
    # GET time slots
    test_endpoint(
        'GET',
        f'{BASE_URL}/time-slots/',
        'Liste des créneaux'
    )
    
    # GET available slots
    today = date.today().isoformat()
    test_endpoint(
        'GET',
        f'{BASE_URL}/time-slots/available_slots/',
        'Créneaux disponibles',
        params={'date': today}
    )
    
    # ========================================================================
    # 3. CLIENT AVAILABILITIES
    # ========================================================================
    print("\n" + "👤"*30)
    print("CLIENT AVAILABILITIES (Disponibilités clients)")
    print("👤"*30)
    
    # GET availabilities
    test_endpoint(
        'GET',
        f'{BASE_URL}/client-availabilities/',
        'Liste des disponibilités'
    )
    
    if is_authenticated:
        # GET my availabilities
        test_endpoint(
            'GET',
            f'{BASE_URL}/client-availabilities/my_availabilities/',
            'Mes disponibilités'
        )
        
        # POST create availability
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        test_endpoint(
            'POST',
            f'{BASE_URL}/client-availabilities/',
            'Créer une disponibilité',
            data={
                "preferred_date": tomorrow,
                "preferred_time_slot": "morning",
                "urgency": "normal",
                "preferred_duration": 60
            }
        )
    
    # ========================================================================
    # 4. SCHEDULES (Principal)
    # ========================================================================
    print("\n" + "📆"*30)
    print("SCHEDULES (Planifications de visites)")
    print("📆"*30)
    
    # GET schedules
    schedules_data = test_endpoint(
        'GET',
        f'{BASE_URL}/schedules/',
        'Liste des planifications'
    )
    
    # GET today's schedules
    test_endpoint(
        'GET',
        f'{BASE_URL}/schedules/today/',
        'Planifications du jour'
    )
    
    # GET upcoming schedules
    test_endpoint(
        'GET',
        f'{BASE_URL}/schedules/upcoming/',
        'Planifications à venir'
    )
    
    # GET calendar view
    start_date = date.today().isoformat()
    end_date = (date.today() + timedelta(days=7)).isoformat()
    calendar_data = test_endpoint(
        'GET',
        f'{BASE_URL}/schedules/calendar_view/',
        'Vue calendrier',
        params={
            'start_date': start_date,
            'end_date': end_date
        }
    )
    
    # Si on a des schedules, tester les actions
    if schedules_data and isinstance(schedules_data, dict):
        results = schedules_data.get('results', [])
        if results and len(results) > 0:
            schedule_id = results[0]['id']
            
            # GET schedule detail
            test_endpoint(
                'GET',
                f'{BASE_URL}/schedules/{schedule_id}/',
                f'Détail planification {schedule_id}'
            )
    
    # ========================================================================
    # 5. CONFLICTS
    # ========================================================================
    print("\n" + "⚠️"*30)
    print("CONFLICTS (Conflits de calendrier)")
    print("⚠️"*30)
    
    # GET conflicts
    test_endpoint(
        'GET',
        f'{BASE_URL}/conflicts/',
        'Liste des conflits'
    )
    
    # ========================================================================
    # 6. PREFERENCES
    # ========================================================================
    print("\n" + "⚙️"*30)
    print("PREFERENCES (Préférences de planification)")
    print("⚙️"*30)
    
    # GET preferences
    test_endpoint(
        'GET',
        f'{BASE_URL}/preferences/',
        'Liste des préférences'
    )
    
    if is_authenticated:
        # GET my preferences
        test_endpoint(
            'GET',
            f'{BASE_URL}/preferences/my_preferences/',
            'Mes préférences'
        )
    
    # ========================================================================
    # 7. METRICS
    # ========================================================================
    print("\n" + "📊"*30)
    print("METRICS (Métriques de planification)")
    print("📊"*30)
    
    # GET metrics
    test_endpoint(
        'GET',
        f'{BASE_URL}/metrics/',
        'Liste des métriques'
    )
    
    if is_authenticated:
        # GET my metrics
        test_endpoint(
            'GET',
            f'{BASE_URL}/metrics/my_metrics/',
            'Mes métriques'
        )
    
    # ========================================================================
    # 8. ADVANCED FEATURES
    # ========================================================================
    print("\n" + "🚀"*30)
    print("ADVANCED FEATURES (Fonctionnalités avancées)")
    print("🚀"*30)
    
    # Calendar view (fonction)
    test_endpoint(
        'GET',
        f'{BASE_URL}/calendar-view/',
        'Vue calendrier (fonction)',
        params={
            'start_date': start_date,
            'end_date': end_date
        }
    )
    
    # ========================================================================
    # RÉSUMÉ
    # ========================================================================
    print("\n" + "="*60)
    print("✅ TESTS TERMINÉS")
    print("="*60)
    print_info("Vérifiez les résultats ci-dessus")
    print_info("Si certains endpoints retournent 403, vérifiez les permissions dans views.py")
    print_info("Si certains endpoints retournent 404, vérifiez les URLs dans urls.py")

if __name__ == "__main__":
    main()

