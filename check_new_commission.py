"""
Script pour vérifier la dernière commission créée et l'utilisateur connecté.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from apps.commissions.models import Commission
from apps.auth.models import User

# Récupérer la dernière commission créée
last_commission = Commission.objects.order_by('-created_at').first()

if last_commission:
    print("=" * 60)
    print("DERNIÈRE COMMISSION CRÉÉE")
    print("=" * 60)
    print(f"ID: {last_commission.id}")
    print(f"Agent: {last_commission.agent.email} (ID: {last_commission.agent.id})")
    print(f"Agence: {last_commission.agency.name} (ID: {last_commission.agency.id})")
    print(f"Type: {last_commission.commission_type}")
    print(f"Montant: {last_commission.commission_amount}")
    print(f"Statut: {last_commission.status}")
    print(f"Créé le: {last_commission.created_at}")
    print()
    
    # Vérifier l'utilisateur fatou.sall
    print("=" * 60)
    print("UTILISATEUR: fatou.sall@digit-hab.com")
    print("=" * 60)
    try:
        user = User.objects.get(email='fatou.sall@digit-hab.com')
        print(f"ID: {user.id}")
        print(f"Rôle: {user.role}")
        
        # Vérifier l'agence de l'utilisateur
        agency = None
        if hasattr(user, 'profile') and user.profile.agency:
            agency = user.profile.agency
        elif hasattr(user, 'agency') and user.agency:
            agency = user.agency
        
        if agency:
            print(f"Agence: {agency.name} (ID: {agency.id})")
        else:
            print("Agence: Aucune")
        
        # Vérifier si la commission est visible pour cet utilisateur
        print()
        print("=" * 60)
        print("VISIBILITÉ DE LA COMMISSION")
        print("=" * 60)
        if agency:
            if last_commission.agency.id == agency.id:
                print("✅ La commission est dans la même agence - DEVRAIT ÊTRE VISIBLE")
            else:
                print("❌ La commission est dans une autre agence - NE SERA PAS VISIBLE")
                print(f"   Commission agence: {last_commission.agency.name} (ID: {last_commission.agency.id})")
                print(f"   User agence: {agency.name} (ID: {agency.id})")
        else:
            if last_commission.agent.id == user.id:
                print("✅ La commission appartient à l'utilisateur - DEVRAIT ÊTRE VISIBLE")
            else:
                print("❌ La commission appartient à un autre agent - NE SERA PAS VISIBLE")
                print(f"   Commission agent: {last_commission.agent.email} (ID: {last_commission.agent.id})")
                print(f"   User: {user.email} (ID: {user.id})")
    except User.DoesNotExist:
        print("❌ Utilisateur non trouvé")
else:
    print("Aucune commission trouvée")
