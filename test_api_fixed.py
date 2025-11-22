#!/usr/bin/env python
"""Script to test API endpoints after fixing AUTH_USER_MODEL."""
import requests
import json
from time import sleep

BASE_URL = "http://127.0.0.1:8000"

print("=" * 70)
print("🧪 TEST DES ENDPOINTS APRÈS CORRECTION")
print("=" * 70)

# Wait for server to be ready
print("\n⏳ Attente du démarrage du serveur...")
sleep(3)

# Test endpoints that were failing before
endpoints_to_test = [
    {
        "name": "Login",
        "method": "POST",
        "url": f"{BASE_URL}/api/auth/login/",
        "data": {"email": "moussa.diop@digit-hab.com", "password": "test123"},
        "auth_required": False
    },
    {
        "name": "Users List",
        "method": "GET",
        "url": f"{BASE_URL}/api/auth/auth/users/",
        "auth_required": True
    },
    {
        "name": "Agencies List",
        "method": "GET",
        "url": f"{BASE_URL}/api/auth/auth/agencies/",
        "auth_required": True
    },
    {
        "name": "Properties List",
        "method": "GET",
        "url": f"{BASE_URL}/api/properties/properties/",
        "auth_required": True
    },
    {
        "name": "Clients List",
        "method": "GET",
        "url": f"{BASE_URL}/api/crm/clients/",
        "auth_required": True
    }
]

# Store token
token = None

for endpoint in endpoints_to_test:
    print(f"\n{'='*70}")
    print(f"📍 Test: {endpoint['name']}")
    print(f"   URL: {endpoint['url']}")
    print(f"   Method: {endpoint['method']}")
    
    try:
        headers = {"Content-Type": "application/json"}
        
        # Add auth if required and available
        if endpoint['auth_required'] and token:
            headers['Authorization'] = f'Bearer {token}'
        
        if endpoint['method'] == 'POST':
            response = requests.post(
                endpoint['url'],
                json=endpoint['data'],
                headers=headers,
                timeout=10
            )
        else:
            response = requests.get(
                endpoint['url'],
                headers=headers,
                timeout=10
            )
        
        # Check response
        status = response.status_code
        
        if status == 200 or status == 201:
            print(f"   ✅ Status: {status} - OK")
            
            # Get token from login
            if endpoint['name'] == 'Login' and status == 200:
                data = response.json()
                if 'access' in data:
                    token = data['access']
                    print(f"   🔑 Token obtenu: {token[:20]}...")
                    if 'user' in data:
                        print(f"   👤 User: {data['user'].get('username', 'N/A')}")
                        print(f"   📧 Email: {data['user'].get('email', 'N/A')}")
            else:
                # Show preview of response
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        if 'count' in data:
                            print(f"   📊 Count: {data['count']}")
                        if 'results' in data and len(data['results']) > 0:
                            print(f"   📄 Premiers résultats: {len(data['results'])} items")
                            first_item = data['results'][0]
                            if 'id' in first_item:
                                print(f"   🔑 Premier ID: {first_item['id']}")
                    elif isinstance(data, list) and len(data) > 0:
                        print(f"   📄 Items: {len(data)}")
                        if 'id' in data[0]:
                            print(f"   🔑 Premier ID: {data[0]['id']}")
                except:
                    print(f"   📝 Response: {response.text[:100]}...")
        
        elif status == 401:
            print(f"   ⚠️  Status: {status} - Non authentifié (normal si pas de token)")
        
        elif status == 403:
            print(f"   ⚠️  Status: {status} - Accès refusé")
        
        else:
            print(f"   ❌ Status: {status} - Erreur")
            print(f"   📝 Response: {response.text[:200]}")
    
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Erreur: Le serveur n'est pas démarré")
        print(f"   💡 Lancez: python manage.py runserver")
        break
    
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")

print(f"\n{'='*70}")
print("✅ Tests terminés!")
print("=" * 70)

if token:
    print("\n💡 TOUS LES ENDPOINTS FONCTIONNENT ! 🎉")
else:
    print("\n⚠️  Le serveur doit être démarré pour les tests complets.")

