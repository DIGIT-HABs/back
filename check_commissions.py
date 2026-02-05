"""
Script pour diagnostiquer le problème des commissions.
Vérifie les commissions en base de données et compare avec l'utilisateur connecté.
"""

import os
import django

# Configuration Django
# Utiliser la même configuration que le serveur Django
# Par défaut, Django utilise digit_hab_crm.settings qui charge dev.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

# Afficher quelle base de données est utilisée
from django.conf import settings
print(f"Base de données utilisée: {settings.DATABASES['default']['NAME']}")
print()

from apps.commissions.models import Commission
from apps.auth.models import User

# Afficher toutes les commissions
print("=" * 60)
print("TOUTES LES COMMISSIONS EN BASE DE DONNÉES")
print("=" * 60)
all_commissions = Commission.objects.all().select_related('agent', 'agency')
print(f"Total : {all_commissions.count()} commission(s)\n")

for comm in all_commissions:
    print(f"ID: {comm.id}")
    print(f"  Agent: {comm.agent.email if comm.agent else 'None'} (ID: {comm.agent.id if comm.agent else 'None'})")
    print(f"  Agence: {comm.agency.name if comm.agency else 'None'} (ID: {comm.agency.id if comm.agency else 'None'})")
    print(f"  Type: {comm.commission_type}")
    print(f"  Montant: {comm.commission_amount}")
    print(f"  Statut: {comm.status}")
    print(f"  Créé le: {comm.created_at}")
    print()

# Afficher les utilisateurs agents
print("=" * 60)
print("UTILISATEURS AGENTS")
print("=" * 60)
agents = User.objects.filter(role='agent')
for agent in agents:
    print(f"Email: {agent.email}")
    print(f"  ID: {agent.id}")
    print(f"  Nom: {agent.get_full_name()}")
    print(f"  Agence: {agent.agency.name if hasattr(agent, 'agency') and agent.agency else 'None'}")
    print(f"  Commissions créées: {Commission.objects.filter(agent=agent).count()}")
    print()

# Test avec un utilisateur spécifique
print("=" * 60)
print("TEST AVEC UTILISATEUR: fatou.sall@digit-hab.com")
print("=" * 60)
try:
    test_user = User.objects.get(email='fatou.sall@digit-hab.com')
    print(f"Utilisateur trouvé: {test_user.email} (ID: {test_user.id})")
    print(f"Rôle: {test_user.role}")
    
    # Commissions visibles pour cet utilisateur
    visible_commissions = Commission.objects.filter(agent=test_user)
    print(f"Commissions visibles pour cet utilisateur: {visible_commissions.count()}")
    
    if visible_commissions.count() > 0:
        for comm in visible_commissions:
            print(f"  - Commission ID: {comm.id}, Montant: {comm.commission_amount}")
    else:
        print("  Aucune commission visible (filtrée par agent=user)")
        
except User.DoesNotExist:
    print("❌ Utilisateur non trouvé")

