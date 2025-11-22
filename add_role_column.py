#!/usr/bin/env python
"""Script to add 'role' column to custom_auth_user table."""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

from django.db import connection

print("=" * 70)
print("🔧 AJOUT DE LA COLONNE 'role' À LA TABLE custom_auth_user")
print("=" * 70)

with connection.cursor() as cursor:
    try:
        # Add role column
        print("\n📝 Ajout de la colonne 'role'...")
        cursor.execute("""
            ALTER TABLE custom_auth_user 
            ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'client'
        """)
        
        print("   ✅ Colonne 'role' ajoutée avec succès !")
        
        # Update existing users to have 'agent' role
        print("\n📝 Mise à jour des utilisateurs existants en tant qu''agent'...")
        cursor.execute("""
            UPDATE custom_auth_user 
            SET role = 'agent'
        """)
        
        rows_updated = cursor.rowcount
        print(f"   ✅ {rows_updated} utilisateurs mis à jour !")
        
        # Set superusers as admin
        print("\n📝 Mise à jour des superusers en tant qu''admin'...")
        cursor.execute("""
            UPDATE custom_auth_user 
            SET role = 'admin'
            WHERE is_superuser = 1
        """)
        
        admin_count = cursor.rowcount
        print(f"   ✅ {admin_count} administrateurs mis à jour !")
        
    except Exception as e:
        print(f"\n   ❌ Erreur : {str(e)}")
        if "duplicate column name" in str(e).lower():
            print("   ℹ️  La colonne 'role' existe déjà !")
        sys.exit(1)

# Verify the column was added
print("\n" + "=" * 70)
print("🔍 VÉRIFICATION")
print("=" * 70)

with connection.cursor() as cursor:
    cursor.execute("PRAGMA table_info(custom_auth_user);")
    columns = cursor.fetchall()
    
    role_exists = False
    for column in columns:
        col_id, col_name, col_type, not_null, default_value, pk = column
        if col_name == 'role':
            role_exists = True
            print(f"\n✅ Colonne 'role' confirmée :")
            print(f"   Type: {col_type}")
            print(f"   Default: {default_value}")
            break
    
    if not role_exists:
        print("\n❌ Erreur : La colonne 'role' n'a pas été trouvée !")
        sys.exit(1)
    
    # Show user roles
    cursor.execute("SELECT username, role, is_superuser FROM custom_auth_user")
    users = cursor.fetchall()
    
    print(f"\n📊 Utilisateurs dans la base ({len(users)}) :")
    for username, role, is_superuser in users:
        super_badge = " [SUPERUSER]" if is_superuser else ""
        print(f"   - {username:<20} → {role}{super_badge}")

print("\n" + "=" * 70)
print("✅ TERMINÉ ! Le champ 'role' est maintenant disponible.")
print("=" * 70)



