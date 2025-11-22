#!/usr/bin/env python
"""
Script pour vérifier et corriger le mot de passe de l'utilisateur.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from apps.auth.models import User

# Email à vérifier
email = "moussa.diop@digit-hab.com"
password = "test123"

print(f"\n{'='*60}")
print(f"Vérification de l'utilisateur : {email}")
print(f"{'='*60}\n")

# Chercher l'utilisateur
try:
    user = User.objects.get(email=email)
    print(f"✅ Utilisateur trouvé:")
    print(f"   - ID: {user.id}")
    print(f"   - Username: {user.username}")
    print(f"   - Email: {user.email}")
    print(f"   - First Name: {user.first_name}")
    print(f"   - Last Name: {user.last_name}")
    print(f"   - Is Active: {user.is_active}")
    print(f"   - Has usable password: {user.has_usable_password()}")
    
    # Vérifier le mot de passe actuel
    if user.check_password(password):
        print(f"\n✅ Le mot de passe '{password}' est correct!")
    else:
        print(f"\n❌ Le mot de passe '{password}' est incorrect!")
        print(f"\n🔧 Réinitialisation du mot de passe...")
        user.set_password(password)
        user.save()
        print(f"✅ Mot de passe réinitialisé avec succès!")
        
        # Vérifier à nouveau
        if user.check_password(password):
            print(f"✅ Vérification: Le mot de passe fonctionne maintenant!")
        else:
            print(f"❌ Erreur: Le mot de passe ne fonctionne toujours pas!")
    
    print(f"\n{'='*60}")
    print("🎉 Script terminé avec succès!")
    print(f"{'='*60}\n")
    
except User.DoesNotExist:
    print(f"❌ Utilisateur avec l'email '{email}' n'existe pas!")
    print(f"\n🔧 Création de l'utilisateur...")
    
    # Créer l'utilisateur
    user = User.objects.create_user(
        username='agent1',
        email=email,
        password=password,
        first_name='Moussa',
        last_name='Diop',
        role='agent',
        is_active=True
    )
    
    print(f"✅ Utilisateur créé avec succès!")
    print(f"   - ID: {user.id}")
    print(f"   - Username: {user.username}")
    print(f"   - Email: {user.email}")
    print(f"\n{'='*60}")
    print("🎉 Script terminé avec succès!")
    print(f"{'='*60}\n")

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

