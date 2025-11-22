#!/usr/bin/env python
"""Script to verify which User model is being used."""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.conf import settings

print("=" * 60)
print("🔍 VÉRIFICATION DU MODÈLE USER")
print("=" * 60)

# Check settings
print(f"\n📄 AUTH_USER_MODEL dans settings:")
print(f"   {settings.AUTH_USER_MODEL}")

# Get actual model
User = get_user_model()
print(f"\n📦 Modèle User chargé par Django:")
print(f"   App: {User._meta.app_label}")
print(f"   Model: {User._meta.model_name}")
print(f"   Label: {User._meta.label}")
print(f"   Table: {User._meta.db_table}")

# Check ID field
id_field = User._meta.get_field('id')
print(f"\n🔑 Type du champ ID:")
print(f"   Type: {type(id_field).__name__}")
print(f"   Internal Type: {id_field.get_internal_type()}")

# Check if users exist
from apps.auth.models import User as CustomUser
custom_users_count = CustomUser.objects.count()
print(f"\n👥 Utilisateurs dans apps.auth.models.User:")
print(f"   Count: {custom_users_count}")

if custom_users_count > 0:
    first_user = CustomUser.objects.first()
    print(f"   Premier user ID: {first_user.id}")
    print(f"   Type ID: {type(first_user.id)}")

print("\n" + "=" * 60)
print("✅ Analyse terminée!")
print("=" * 60)

