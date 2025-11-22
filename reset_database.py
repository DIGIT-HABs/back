"""
Script pour réinitialiser la base de données et créer des données de test.
⚠️ ATTENTION: Supprime toutes les données existantes !
"""

import os
import sys
import subprocess
from pathlib import Path

# Couleurs
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(message):
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")

def run_command(command, description):
    """Execute une commande."""
    print_info(f"{description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print_success(f"{description} - OK")
        if result.stdout and result.stdout.strip():
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"{description} - Échec")
        if e.stderr:
            print(e.stderr)
        return False

def main():
    print_header("🔄 RÉINITIALISATION DE LA BASE DE DONNÉES")
    
    print_warning("⚠️  ATTENTION: Cette opération va SUPPRIMER TOUTES LES DONNÉES !")
    print_info("La base de données sera recréée avec un schéma propre.")
    print()
    
    response = input(f"{Colors.BOLD}Continuer? (tapez 'YES' en majuscules): {Colors.ENDC}")
    if response != 'YES':
        print_warning("Opération annulée")
        sys.exit(0)
    
    # Étape 1: Supprimer la base de données
    print_header("📦 ÉTAPE 1: Suppression de la base de données")
    
    db_file = Path("digit_hab_crm/db.sqlite3")
    backup_file = Path("digit_hab_crm/db.sqlite3.backup")
    
    if db_file.exists():
        try:
            db_file.unlink()
            print_success("Base de données supprimée")
        except Exception as e:
            print_error(f"Impossible de supprimer la base: {e}")
            sys.exit(1)
    else:
        print_info("Aucune base de données existante")
    
    if backup_file.exists():
        try:
            backup_file.unlink()
            print_info("Backup supprimé")
        except:
            pass
    
    # Étape 2: Supprimer tous les fichiers de migration (sauf __init__.py)
    print_header("📝 ÉTAPE 2: Nettoyage des migrations")
    
    apps_dir = Path("apps")
    migration_deleted = 0
    
    for app_path in apps_dir.iterdir():
        if app_path.is_dir():
            migrations_dir = app_path / "migrations"
            if migrations_dir.exists():
                for migration_file in migrations_dir.iterdir():
                    if migration_file.name != "__init__.py" and migration_file.suffix == ".py":
                        try:
                            migration_file.unlink()
                            migration_deleted += 1
                        except Exception as e:
                            print_warning(f"Impossible de supprimer {migration_file}: {e}")
    
    print_success(f"{migration_deleted} fichiers de migration supprimés")
    
    # Étape 3: Créer les nouvelles migrations
    print_header("📝 ÉTAPE 3: Création des nouvelles migrations")
    
    if not run_command("python manage.py makemigrations", "Création des migrations"):
        print_error("Échec de la création des migrations")
        sys.exit(1)
    
    # Étape 4: Appliquer les migrations
    print_header("⚙️ ÉTAPE 4: Application des migrations")
    
    if not run_command("python manage.py migrate", "Application des migrations"):
        print_error("Échec de l'application des migrations")
        sys.exit(1)
    
    # Étape 5: Créer un superuser
    print_header("👤 ÉTAPE 5: Création du superuser")
    
    print_info("Création automatique d'un superuser admin/admin123")
    create_superuser_cmd = (
        'python manage.py shell -c "'
        'from apps.auth.models import User; '
        "User.objects.create_superuser("
        "username='admin', "
        "email='admin@digit-hab.com', "
        "password='admin123', "
        "first_name='Admin', "
        "last_name='Digit-Hab', "
        "role='admin'"
        ')"'
    )
    
    if run_command(create_superuser_cmd, "Création du superuser"):
        print_success("✅ Superuser créé: admin / admin123")
    
    # Étape 6: Créer des données de test (optionnel)
    print_header("📊 ÉTAPE 6: Données de test (optionnel)")
    
    response = input(f"{Colors.BOLD}Créer des données de test? (y/N): {Colors.ENDC}")
    if response.lower() == 'y':
        test_data_file = Path("create_test_data.py")
        if test_data_file.exists():
            run_command("python create_test_data.py", "Création des données de test")
        else:
            print_warning("Fichier create_test_data.py introuvable")
    
    # Résumé final
    print_header("✅ TERMINÉ !")
    
    print_success("Base de données réinitialisée avec succès")
    print()
    print_info("🔑 Identifiants admin:")
    print(f"   Username: {Colors.BOLD}admin{Colors.ENDC}")
    print(f"   Password: {Colors.BOLD}admin123{Colors.ENDC}")
    print()
    print_info("🚀 Lancer le serveur:")
    print(f"   {Colors.BOLD}python manage.py runserver{Colors.ENDC}")
    print()
    print_info("📱 Admin:")
    print(f"   {Colors.BOLD}http://localhost:8000/admin/{Colors.ENDC}")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Opération interrompue{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Erreur: {e}")
        sys.exit(1)



