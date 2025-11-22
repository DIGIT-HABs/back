#!/usr/bin/env python
"""Script to check if 'role' column exists in custom_auth_user table."""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from django.db import connection

print("=" * 60)
print("🔍 VÉRIFICATION DE LA COLONNE 'role'")
print("=" * 60)

# Get table schema
with connection.cursor() as cursor:
    cursor.execute("PRAGMA table_info(custom_auth_user);")
    columns = cursor.fetchall()
    
    print("\n📋 Colonnes de la table 'custom_auth_user':\n")
    
    role_exists = False
    for column in columns:
        col_id, col_name, col_type, not_null, default_value, pk = column
        print(f"   {col_name:<30} {col_type:<15} {'NOT NULL' if not_null else ''}")
        if col_name == 'role':
            role_exists = True
            print(f"      ✅ TROUVÉ ! Default: {default_value}")
    
    print("\n" + "=" * 60)
    if role_exists:
        print("✅ Le champ 'role' EXISTE dans la base de données !")
    else:
        print("❌ Le champ 'role' N'EXISTE PAS dans la base de données !")
        print("   💡 Il faut appliquer la migration ou recréer la table.")
    print("=" * 60)



