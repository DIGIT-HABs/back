#!/usr/bin/env python
"""Script to test CRM API endpoints after adding agency property."""
import requests
import json
from time import sleep

BASE_URL = "http://127.0.0.1:8000"

print("=" * 70)
print("🧪 TEST DES ENDPOINTS CRM")
print("=" * 70)

# Test endpoints
endpoints_to_test = [
    {
        "name": "Login",
        "method": "POST",
        "url": f"{BASE_URL}/api/auth/login/",
        "data": {"email": "moussa.diop@digit-hab.com", "password": "test123"},
        "auth_required": False
    },
    {
        "name": "CRM - Client Profiles",
        "method": "GET",
        "url": f"{BASE_URL}/api/crm/clients/",
        "auth_required": True
    },
    {
        "name": "CRM - Interactions",
        "method": "GET",
        "url": f"{BASE_URL}/api/crm/interactions/",
        "auth_required": True
    },
    {
        "name": "CRM - Leads",
        "method": "GET",
        "url": f"{BASE_URL}/api/crm/leads/",
        "auth_required": True
    },
    {
        "name": "CRM - Property Interests",
        "method": "GET",
        "url": f"{BASE_URL}/api/crm/interests/",
        "auth_required": True
    },
    {
        "name": "Properties List",
        "method": "GET",
        "url": f"{BASE_URL}/api/properties/properties/",
        "auth_required": True
    }
]

# Store token
token = None

for endpoint in endpoints_to_test:
    print(f"\n{'='*70}")
    print(f"📍 Test: {endpoint['name']}")
    print(f"   URL: {endpoint['url']}")
    
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
                    print(f"   🔑 Token obtenu")
                    if 'user' in data:
                        user = data['user']
                        print(f"   👤 User: {user.get('username', 'N/A')}")
                        print(f"   🎭 Role: {user.get('role', 'N/A')}")
            else:
                # Show preview of response
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        if 'count' in data:
                            print(f"   📊 Count: {data['count']}")
                        if 'results' in data:
                            results_count = len(data['results'])
                            print(f"   📄 Results: {results_count} items")
                            if results_count > 0:
                                first_item = data['results'][0]
                                if 'id' in first_item:
                                    print(f"   🔑 Premier ID: {first_item['id']}")
                    elif isinstance(data, list):
                        print(f"   📄 Items: {len(data)}")
                except:
                    print(f"   📝 Response OK")
        
        elif status == 401:
            print(f"   ⚠️  Status: {status} - Non authentifié")
        
        elif status == 403:
            print(f"   ⚠️  Status: {status} - Accès refusé")
        
        elif status == 500:
            print(f"   ❌ Status: {status} - Erreur serveur")
            try:
                error_text = response.text[:300]
                if "AttributeError" in error_text:
                    if "'User' object has no attribute 'agency'" in error_text:
                        print(f"   🐛 Erreur: user.agency manquant (propriété non appliquée?)")
                    else:
                        print(f"   🐛 AttributeError détecté")
                else:
                    print(f"   📝 Erreur: {error_text[:100]}...")
            except:
                pass
        
        else:
            print(f"   ❌ Status: {status}")
    
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Erreur: Le serveur n'est pas démarré")
        print(f"   💡 Lancez: python manage.py runserver")
        break
    
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")

print(f"\n{'='*70}")
print("✅ Tests terminés!")
print("=" * 70)



