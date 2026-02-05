"""
Script de test pour tous les nouveaux endpoints créés dans la Phase 1.
Teste les endpoints clients, leads et commissions.
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "fatou.sall@digit-hab.com"
TEST_PASSWORD = "test123"

# Couleurs pour l'affichage
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class EndpointTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_id = None
        self.agency_id = None
        self.client_id = None
        self.lead_id = None
        self.commission_id = None
        self.payment_id = None
        
    def print_header(self, text):
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{text:^60}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
    
    def print_success(self, text):
        print(f"{GREEN}✅ {text}{RESET}")
    
    def print_error(self, text):
        print(f"{RED}❌ {text}{RESET}")
    
    def print_info(self, text):
        print(f"{YELLOW}ℹ️  {text}{RESET}")
    
    def make_request(self, method, endpoint, data=None, params=None, headers=None):
        """Faire une requête HTTP."""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        headers['Content-Type'] = 'application/json'
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
            return response
        except requests.exceptions.ConnectionError as e:
            self.print_error(f"Erreur de connexion : Impossible de se connecter au serveur.")
            self.print_info("💡 Vérifiez que le serveur Django est démarré : python manage.py runserver")
            return None
        except requests.exceptions.Timeout as e:
            self.print_error(f"Timeout : La requête a pris trop de temps (>10s).")
            return None
        except Exception as e:
            self.print_error(f"Erreur : {str(e)}")
            import traceback
            print(f"Détails : {traceback.format_exc()}")
            return None
    
    def test_login(self):
        """Test de connexion."""
        self.print_header("TEST AUTHENTIFICATION")
        
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = self.make_request('POST', '/auth/login/', data=login_data)
        
        if response and response.status_code == 200:
            data = response.json()
            self.token = data.get('access')
            self.print_success("Connexion réussie")
            return True
        else:
            self.print_error(f"Échec de connexion : {response.status_code if response else 'No response'}")
            if response:
                print(f"Réponse : {response.text}")
            return False
    
    def test_get_user_info(self):
        """Récupérer les infos de l'utilisateur connecté."""
        response = self.make_request('GET', '/auth/users/me/')
        
        if response and response.status_code == 200:
            data = response.json()
            self.user_id = data.get('id')
            # Récupérer l'agence depuis agency_id (nouveau champ)
            self.agency_id = data.get('agency_id')
            if not self.agency_id:
                # Fallback : essayer de récupérer depuis le profil
                self.print_info("Agence non trouvée dans la réponse, tentative via profil...")
                # On peut essayer de récupérer via l'endpoint profile
                profile_response = self.make_request('GET', '/auth/auth/profiles/')
                if profile_response and profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    if isinstance(profile_data, list) and len(profile_data) > 0:
                        self.agency_id = profile_data[0].get('agency')
                    elif isinstance(profile_data, dict):
                        self.agency_id = profile_data.get('agency')
            
            self.print_success(f"Utilisateur : {data.get('username')} (ID: {self.user_id})")
            if self.agency_id:
                self.print_success(f"Agence ID : {self.agency_id}")
            else:
                self.print_info("⚠️  Aucune agence associée - certains tests seront ignorés")
            return True
        else:
            if response:
                self.print_error(f"Échec récupération user info : {response.status_code}")
                print(f"Réponse : {response.text}")
        return False
    
    # ==================== TESTS CLIENTS ====================
    
    def test_clients_list(self):
        """Test GET /api/crm/clients/"""
        self.print_header("TEST ENDPOINTS CLIENTS")
        
        response = self.make_request('GET', '/crm/clients/')
        
        if response and response.status_code == 200:
            data = response.json()
            clients = data.get('results', data) if isinstance(data, dict) else data
            
            if isinstance(clients, list) and len(clients) > 0:
                self.client_id = clients[0].get('id')
                self.print_success(f"Liste clients : {len(clients)} client(s) trouvé(s)")
                return True
            else:
                self.print_info("Aucun client trouvé (normal si base vide)")
                return True
        else:
            self.print_error(f"Échec : {response.status_code if response else 'No response'}")
            return False
    
    def test_client_interactions(self):
        """Test GET /api/crm/clients/{id}/interactions/"""
        if not self.client_id:
            self.print_info("Pas de client ID, test ignoré")
            return True
        
        response = self.make_request('GET', f'/crm/clients/{self.client_id}/interactions/')
        
        if response and response.status_code == 200:
            data = response.json()
            interactions = data if isinstance(data, list) else data.get('results', [])
            self.print_success(f"Interactions client : {len(interactions)} interaction(s)")
            return True
        else:
            self.print_error(f"Échec : {response.status_code if response else 'No response'}")
            return False
    
    def test_client_add_interaction(self):
        """Test POST /api/crm/clients/{id}/interactions/"""
        if not self.client_id:
            self.print_info("Pas de client ID, test ignoré")
            return True
        
        interaction_data = {
            "agent_id": str(self.user_id),
            "interaction_type": "call",
            "channel": "phone",
            "subject": "Test interaction",
            "content": "Ceci est un test d'interaction",
            "priority": "medium",
            "status": "scheduled"
        }
        
        response = self.make_request('POST', f'/crm/clients/{self.client_id}/add_interaction/', data=interaction_data)
        
        if response and response.status_code in [200, 201]:
            self.print_success("Interaction ajoutée avec succès")
            return True
        else:
            self.print_error(f"Échec : {response.status_code if response else 'No response'}")
            if response:
                print(f"Réponse : {response.text}")
            return False
    
    def test_client_stats(self):
        """Test GET /api/crm/clients/{id}/stats/"""
        if not self.client_id:
            self.print_info("Pas de client ID, test ignoré")
            return True
        
        response = self.make_request('GET', f'/crm/clients/{self.client_id}/stats/')
        
        if response and response.status_code == 200:
            data = response.json()
            self.print_success(f"Stats client récupérées : {data.get('interactions', {}).get('total', 0)} interactions")
            return True
        else:
            self.print_error(f"Échec : {response.status_code if response else 'No response'}")
            return False
    
    def test_client_contact(self):
        """Test POST /api/crm/clients/{id}/contact/"""
        if not self.client_id:
            self.print_info("Pas de client ID, test ignoré")
            return True
        
        contact_data = {
            "method": "email",
            "subject": "Test contact",
            "message": "Ceci est un test de contact"
        }
        
        response = self.make_request('POST', f'/crm/clients/{self.client_id}/contact/', data=contact_data)
        
        if response and response.status_code in [200, 201]:
            self.print_success("Action de contact créée avec succès")
            return True
        else:
            self.print_error(f"Échec : {response.status_code if response else 'No response'}")
            if response:
                print(f"Réponse : {response.text}")
            return False
    
    # ==================== TESTS LEADS ====================
    
    def test_leads_list(self):
        """Test GET /api/crm/leads/"""
        self.print_header("TEST ENDPOINTS LEADS")
        
        response = self.make_request('GET', '/crm/leads/')
        
        if response is None:
            self.print_error("Aucune réponse du serveur. Vérifiez que Django est démarré.")
            return False
        
        if response.status_code == 200:
            data = response.json()
            leads = data.get('results', data) if isinstance(data, dict) else data
            
            if isinstance(leads, list) and len(leads) > 0:
                self.lead_id = leads[0].get('id')
                self.print_success(f"Liste leads : {len(leads)} lead(s) trouvé(s)")
                return True
            else:
                self.print_info("Aucun lead trouvé (normal si base vide)")
                # Créer un lead de test
                return self.test_create_lead()
        else:
            self.print_error(f"Échec : {response.status_code}")
            if response.status_code >= 500:
                self.print_error("Erreur serveur (500) - Vérifiez les logs Django")
            print(f"Réponse : {response.text[:200]}")
            return False
    
    def test_create_lead(self):
        """Créer un lead de test."""
        if not self.agency_id:
            self.print_info("Pas d'agence ID, test ignoré")
            return True
        
        lead_data = {
            "first_name": "Test",
            "last_name": "Lead",
            "email": "testlead@example.com",
            "phone": "+221771234567",
            "source": "website",
            "status": "new",
            "qualification": "warm",
            "agency_id": str(self.agency_id),
            "property_type_interest": "appartement",
            "budget_range": "50000000-100000000",
            "location_interest": "Dakar",
            "notes": "Lead de test"
        }
        
        response = self.make_request('POST', '/crm/leads/', data=lead_data)
        
        if response and response.status_code in [200, 201]:
            data = response.json()
            self.lead_id = data.get('id')
            self.print_success(f"Lead créé avec succès (ID: {self.lead_id})")
            return True
        else:
            self.print_error(f"Échec création lead : {response.status_code if response else 'No response'}")
            if response:
                print(f"Réponse : {response.text}")
            return False
    
    def test_lead_qualify(self):
        """Test POST /api/crm/leads/{id}/qualify/"""
        if not self.lead_id:
            self.print_info("Pas de lead ID, test ignoré")
            return True
        
        qualify_data = {
            "qualification": "hot",
            "notes": "Lead très intéressé"
        }
        
        response = self.make_request('POST', f'/crm/leads/{self.lead_id}/qualify/', data=qualify_data)
        
        if response and response.status_code == 200:
            data = response.json()
            self.print_success(f"Lead qualifié : {data.get('qualification')} (score: {data.get('score')})")
            return True
        else:
            self.print_error(f"Échec : {response.status_code if response else 'No response'}")
            if response:
                print(f"Réponse : {response.text}")
            return False
    
    def test_leads_pipeline(self):
        """Test GET /api/crm/leads/pipeline/"""
        response = self.make_request('GET', '/crm/leads/pipeline/')
        
        if response is None:
            self.print_error("Aucune réponse du serveur. Vérifiez que Django est démarré.")
            return False
        
        if response.status_code == 200:
            data = response.json()
            pipeline = data.get('pipeline', {})
            metrics = data.get('metrics', {})
            
            self.print_success(f"Pipeline récupéré : {metrics.get('total_leads', 0)} leads")
            for stage, info in pipeline.items():
                count = info.get('count', 0)
                if count > 0:
                    print(f"  - {info.get('title', stage)}: {count} lead(s)")
            return True
        else:
            self.print_error(f"Échec : {response.status_code}")
            if response.status_code >= 500:
                self.print_error("Erreur serveur (500) - Vérifiez les logs Django")
            print(f"Réponse : {response.text[:200]}")
            return False
    
    # ==================== TESTS COMMISSIONS ====================
    
    def test_commissions_list(self):
        """Test GET /api/commissions/commissions/"""
        self.print_header("TEST ENDPOINTS COMMISSIONS")
        
        response = self.make_request('GET', '/commissions/commissions/')
        
        if response and response.status_code == 200:
            data = response.json()
            commissions = data.get('results', data) if isinstance(data, dict) else data
            
            if isinstance(commissions, list):
                self.print_success(f"Liste commissions : {len(commissions)} commission(s)")
                if len(commissions) > 0:
                    self.commission_id = commissions[0].get('id')
                return True
            else:
                self.print_info("Aucune commission trouvée (normal si base vide)")
                return True
        else:
            self.print_error(f"Échec : {response.status_code if response else 'No response'}")
            return False
    
    def test_create_commission(self):
        """Créer une commission de test."""
        if not self.agency_id or not self.user_id:
            self.print_info("Pas d'agence ou user ID, test ignoré")
            return True
        
        commission_data = {
            "agent_id": str(self.user_id),
            "agency_id": str(self.agency_id),
            "commission_type": "sale",
            "base_amount": "100000000",
            "commission_rate": "3.00",
            "status": "pending",
            "notes": "Commission de test"
        }
        
        response = self.make_request('POST', '/commissions/commissions/', data=commission_data)
        
        if response is None:
            self.print_error("Aucune réponse du serveur. Vérifiez que Django est démarré.")
            return False
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.commission_id = data.get('id')
            commission_amount = data.get('commission_amount')
            self.print_success(f"Commission créée : {commission_amount} XOF (ID: {self.commission_id})")
            return True
        else:
            self.print_error(f"Échec création commission : {response.status_code}")
            if response.status_code >= 500:
                self.print_error("Erreur serveur (500) - Vérifiez les logs Django")
            print(f"Réponse : {response.text[:500]}")
            return False
    
    def test_commission_stats(self):
        """Test GET /api/commissions/commissions/stats/"""
        response = self.make_request('GET', '/commissions/commissions/stats/')
        
        if response and response.status_code == 200:
            data = response.json()
            self.print_success(f"Stats commissions :")
            print(f"  - Total : {data.get('total_commissions', 0)}")
            print(f"  - Montant total : {data.get('total_amount', 0)} XOF")
            print(f"  - En attente : {data.get('pending_amount', 0)} XOF")
            print(f"  - Payées : {data.get('paid_amount', 0)} XOF")
            return True
        else:
            self.print_error(f"Échec : {response.status_code if response else 'No response'}")
            return False
    
    def test_commission_pending(self):
        """Test GET /api/commissions/commissions/pending/"""
        response = self.make_request('GET', '/commissions/commissions/pending/')
        
        if response and response.status_code == 200:
            data = response.json()
            commissions = data if isinstance(data, list) else data.get('results', [])
            self.print_success(f"Commissions en attente : {len(commissions)}")
            return True
        else:
            self.print_error(f"Échec : {response.status_code if response else 'No response'}")
            return False
    
    def test_payments_list(self):
        """Test GET /api/commissions/payments/"""
        response = self.make_request('GET', '/commissions/payments/')
        
        if response and response.status_code == 200:
            data = response.json()
            payments = data.get('results', data) if isinstance(data, dict) else data
            
            if isinstance(payments, list):
                self.print_success(f"Liste paiements : {len(payments)} paiement(s)")
                if len(payments) > 0:
                    self.payment_id = payments[0].get('id')
                return True
            else:
                self.print_info("Aucun paiement trouvé (normal si base vide)")
                return True
        else:
            self.print_error(f"Échec : {response.status_code if response else 'No response'}")
            return False
    
    def test_payment_history(self):
        """Test GET /api/commissions/payments/history/"""
        response = self.make_request('GET', '/commissions/payments/history/')
        
        if response and response.status_code == 200:
            data = response.json()
            payments = data if isinstance(data, list) else data.get('results', [])
            self.print_success(f"Historique paiements : {len(payments)} paiement(s) complété(s)")
            return True
        else:
            self.print_error(f"Échec : {response.status_code if response else 'No response'}")
            return False
    
    # ==================== RUN ALL TESTS ====================
    
    def run_all_tests(self):
        """Exécuter tous les tests."""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{'TEST COMPLET DES NOUVEAUX ENDPOINTS':^60}{RESET}")
        print(f"{BLUE}{'Phase 1 - Fondations':^60}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        
        results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Authentification
        if not self.test_login():
            self.print_error("Impossible de continuer sans authentification")
            return results
        
        if not self.test_get_user_info():
            self.print_error("Impossible de récupérer les infos utilisateur")
            return results
        
        # Tests Clients
        tests_clients = [
            ("Liste clients", self.test_clients_list),
            ("Interactions client", self.test_client_interactions),
            ("Ajouter interaction", self.test_client_add_interaction),
            ("Stats client", self.test_client_stats),
            ("Contact client", self.test_client_contact),
        ]
        
        for name, test_func in tests_clients:
            try:
                if test_func():
                    results['passed'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                self.print_error(f"Erreur dans {name}: {str(e)}")
                results['failed'] += 1
        
        # Tests Leads
        tests_leads = [
            ("Liste leads", self.test_leads_list),
            ("Qualifier lead", self.test_lead_qualify),
            ("Pipeline leads", self.test_leads_pipeline),
        ]
        
        for name, test_func in tests_leads:
            try:
                if test_func():
                    results['passed'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                self.print_error(f"Erreur dans {name}: {str(e)}")
                results['failed'] += 1
        
        # Tests Commissions
        tests_commissions = [
            ("Liste commissions", self.test_commissions_list),
            ("Créer commission", self.test_create_commission),
            ("Stats commissions", self.test_commission_stats),
            ("Commissions en attente", self.test_commission_pending),
            ("Liste paiements", self.test_payments_list),
            ("Historique paiements", self.test_payment_history),
        ]
        
        for name, test_func in tests_commissions:
            try:
                if test_func():
                    results['passed'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                self.print_error(f"Erreur dans {name}: {str(e)}")
                results['failed'] += 1
        
        # Résumé
        self.print_header("RÉSUMÉ DES TESTS")
        print(f"{GREEN}✅ Tests réussis : {results['passed']}{RESET}")
        print(f"{RED}❌ Tests échoués : {results['failed']}{RESET}")
        print(f"{YELLOW}⏭️  Tests ignorés : {results['skipped']}{RESET}")
        print(f"\nTotal : {results['passed'] + results['failed'] + results['skipped']} tests")
        
        return results


if __name__ == "__main__":
    tester = EndpointTester()
    tester.run_all_tests()

