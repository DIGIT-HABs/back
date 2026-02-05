"""
Script simple pour tester un endpoint spécifique et voir l'erreur exacte.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "fatou.sall@digit-hab.com"
TEST_PASSWORD = "test123"

def test_endpoint():
    # 1. Login
    print("1. Connexion...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login/",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Erreur login : {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json().get('access')
    print(f"✅ Token obtenu : {token[:20]}...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 2. Test endpoint leads
    print("\n2. Test GET /api/crm/leads/...")
    try:
        response = requests.get(
            f"{BASE_URL}/crm/leads/",
            headers=headers,
            timeout=10
        )
        print(f"Status : {response.status_code}")
        if response.status_code == 200:
            print("✅ Succès")
            data = response.json()
            print(f"Résultat : {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"❌ Erreur : {response.status_code}")
            print(f"Réponse : {response.text[:500]}")
    except requests.exceptions.ConnectionError:
        print("❌ Erreur de connexion - Le serveur Django n'est pas démarré")
        print("💡 Lancez : python manage.py runserver")
    except Exception as e:
        print(f"❌ Erreur : {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 3. Test endpoint pipeline
    print("\n3. Test GET /api/crm/leads/pipeline/...")
    try:
        response = requests.get(
            f"{BASE_URL}/crm/leads/pipeline/",
            headers=headers,
            timeout=10
        )
        print(f"Status : {response.status_code}")
        if response.status_code == 200:
            print("✅ Succès")
            data = response.json()
            print(f"Résultat : {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"❌ Erreur : {response.status_code}")
            print(f"Réponse : {response.text[:500]}")
    except Exception as e:
        print(f"❌ Erreur : {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 4. Test création commission
    print("\n4. Test POST /api/commissions/commissions/...")
    try:
        # Récupérer user info d'abord
        user_response = requests.get(f"{BASE_URL}/auth/users/me/", headers=headers)
        if user_response.status_code == 200:
            user_data = user_response.json()
            user_id = user_data.get('id')
            agency_id = user_data.get('agency_id')
            
            if agency_id:
                commission_data = {
                    "agent_id": str(user_id),
                    "agency_id": str(agency_id),
                    "commission_type": "sale",
                    "base_amount": "100000000",
                    "commission_rate": "3.00",
                    "status": "pending",
                    "notes": "Commission de test"
                }
                
                response = requests.post(
                    f"{BASE_URL}/commissions/commissions/",
                    headers=headers,
                    json=commission_data,
                    timeout=10
                )
                print(f"Status : {response.status_code}")
                if response.status_code in [200, 201]:
                    print("✅ Succès")
                    data = response.json()
                    print(f"Résultat : {json.dumps(data, indent=2)[:500]}")
                else:
                    print(f"❌ Erreur : {response.status_code}")
                    print(f"Réponse : {response.text[:500]}")
            else:
                print("⚠️  Pas d'agence ID disponible")
        else:
            print(f"❌ Erreur récupération user : {user_response.status_code}")
    except Exception as e:
        print(f"❌ Erreur : {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_endpoint()

