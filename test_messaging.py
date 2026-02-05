"""
Script de test pour l'app messaging (endpoints REST et WebSocket).
"""

import requests
import json
import asyncio
import websockets
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api"
WS_URL = "ws://localhost:8000/ws/messaging/chat"
TEST_EMAIL = "fatou.sall@digit-hab.com"
TEST_PASSWORD = "test123"

# Couleurs
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_rest_api():
    """Test REST API endpoints."""
    print_section("TEST API REST - MESSAGING")
    
    # 1. Login
    print(f"{BLUE}1. Connexion...{RESET}")
    login_response = requests.post(
        f"{BASE_URL}/auth/login/",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    
    if login_response.status_code != 200:
        print(f"{RED}❌ Erreur login : {login_response.status_code}{RESET}")
        print(login_response.text)
        return None
    
    token = login_response.json().get('access')
    print(f"{GREEN}✅ Token obtenu{RESET}")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 2. Get user info
    print(f"\n{BLUE}2. Récupération info utilisateur...{RESET}")
    user_response = requests.get(f"{BASE_URL}/auth/users/me/", headers=headers)
    if user_response.status_code == 200:
        user_data = user_response.json()
        user_id = user_data.get('id')
        print(f"{GREEN}✅ Utilisateur : {user_data.get('email')} (ID: {user_id}){RESET}")
    else:
        print(f"{RED}❌ Erreur récupération user{RESET}")
        return None
    
    # 3. Get or create conversation
    print(f"\n{BLUE}3. Liste des conversations...{RESET}")
    conv_response = requests.get(f"{BASE_URL}/messaging/conversations/", headers=headers)
    if conv_response.status_code != 200:
        print(f"{RED}❌ Erreur : {conv_response.status_code}{RESET}")
        print(conv_response.text)
        return None

    conversations = conv_response.json()
    results = conversations.get('results') or []
    count = conversations.get('count', len(results))
    print(f"{GREEN}✅ Conversations trouvées : {count}{RESET}")

    if results:
        conversation_id = results[0]['id']
        print(f"{GREEN}✅ Utilisation conversation existante : {conversation_id}{RESET}")
        return token, conversation_id

    # Aucune conversation : en créer une (avec soi-même pour le test)
    print(f"{YELLOW}ℹ️  Aucune conversation, création d'une nouvelle...{RESET}")
    create_response = requests.post(
        f"{BASE_URL}/messaging/conversations/create_with_participants/",
        headers=headers,
        json={
            'participant_ids': [str(user_id)],
            'conversation_type': 'direct',
        },
    )
    if create_response.status_code in (200, 201):
        new_conv = create_response.json()
        conversation_id = new_conv.get('id')
        print(f"{GREEN}✅ Conversation créée : {conversation_id}{RESET}")
        return token, conversation_id
    else:
        print(f"{RED}❌ Erreur création conversation : {create_response.status_code}{RESET}")
        print(create_response.text)
        return None


async def test_websocket(token, conversation_id=None):
    """Test WebSocket connection."""
    print_section("TEST WEBSOCKET - TEMPS RÉEL")
    
    if not conversation_id:
        print(f"{YELLOW}⚠️  Pas de conversation ID, test WebSocket ignoré{RESET}")
        print(f"{YELLOW}💡 Créez d'abord une conversation via l'API REST{RESET}")
        return
    
    # Connexion acceptée d'abord; le token est envoyé dans le 1er message (type=auth)
    ws_url = f"{WS_URL}/{conversation_id}/"
    print(f"{BLUE}Connexion WebSocket à : {ws_url}{RESET}")
    print(f"{BLUE}Token : {token[:20]}...{RESET}")

    try:
        # Origin requis par AllowedHostsOriginValidator (sinon 403)
        async with websockets.connect(
            ws_url,
            additional_headers={"Origin": "http://localhost:8000"},
        ) as websocket:
            print(f"{GREEN}✅ Connecté au WebSocket{RESET}")

            # Premier message obligatoire : auth avec le JWT
            print(f"{BLUE}Envoi auth (token JWT)...{RESET}")
            await websocket.send(json.dumps({"type": "auth", "token": token}))
            print(f"{GREEN}✅ Message auth envoyé{RESET}")

            # Attendre la confirmation "connection" (ou erreur)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                if data.get("type") == "error":
                    print(f"{RED}❌ Erreur serveur : {data.get('message')}{RESET}")
                    return
                print(f"{GREEN}✅ Authentifié : {data.get('type')}{RESET}")
                print(f"   {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                print(f"{YELLOW}⚠️  Timeout en attendant la confirmation{RESET}")
            
            # Send a test message
            print(f"\n{BLUE}Envoi d'un message de test...{RESET}")
            test_message = {
                'type': 'message',
                'content': f'Message de test à {datetime.now().strftime("%H:%M:%S")}',
                'message_type': 'text'
            }
            await websocket.send(json.dumps(test_message))
            print(f"{GREEN}✅ Message envoyé{RESET}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"{GREEN}✅ Réponse reçue : {data.get('type')}{RESET}")
                print(f"   {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                print(f"{YELLOW}⚠️  Timeout en attendant la réponse{RESET}")
            
            # Test typing indicator
            print(f"\n{BLUE}Test indicateur de frappe...{RESET}")
            typing_message = {
                'type': 'typing',
                'is_typing': True
            }
            await websocket.send(json.dumps(typing_message))
            print(f"{GREEN}✅ Indicateur de frappe envoyé{RESET}")
            
            await asyncio.sleep(2)
            
            typing_stop = {
                'type': 'typing',
                'is_typing': False
            }
            await websocket.send(json.dumps(typing_stop))
            print(f"{GREEN}✅ Arrêt de la frappe envoyé{RESET}")
            
    except Exception as e:
        if 'status code' in str(e).lower() or '403' in str(e) or '401' in str(e):
            print(f"{RED}❌ Erreur de connexion WebSocket (auth ou refus) : {e}{RESET}")
            print(f"{YELLOW}💡 Vérifiez que le serveur Django Channels est démarré et que le token est valide{RESET}")
        else:
            print(f"{RED}❌ Erreur : {str(e)}{RESET}")
            import traceback
            traceback.print_exc()


def main():
    """Main test function."""
    print(f"\n{'='*60}")
    print(f"  TEST COMPLET - MESSAGING (REST + WebSocket)")
    print(f"{'='*60}\n")
    
    # Test REST API
    result = test_rest_api()
    
    if result:
        token, conversation_id = result
        if conversation_id:
            print(f"\n{BLUE}Démarrage du test WebSocket...{RESET}")
            asyncio.run(test_websocket(token, conversation_id))
        else:
            print(f"\n{YELLOW}ℹ️  Impossible d'obtenir une conversation pour le test WebSocket{RESET}")
    else:
        print(f"\n{RED}❌ Les tests REST ont échoué, impossible de tester WebSocket{RESET}")
    
    print(f"\n{'='*60}")
    print(f"  FIN DES TESTS")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

