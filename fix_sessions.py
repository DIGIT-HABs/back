#!/usr/bin/env python
"""
Script pour nettoyer les sessions et corriger le problème UUID
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from django.contrib.sessions.models import Session

print("\n" + "="*60)
print("NETTOYAGE DES SESSIONS")
print("="*60 + "\n")

# Supprimer toutes les sessions
count = Session.objects.all().count()
print(f"Sessions actuelles : {count}")

if count > 0:
    Session.objects.all().delete()
    print(f"✅ {count} sessions supprimées")
else:
    print("✅ Aucune session à supprimer")

print("\n" + "="*60)
print("✨ TERMINÉ!")
print("="*60 + "\n")

