"""
Script pour appliquer les corrections au projet DIGIT-HAB CRM
Ce script crée et applique les migrations nécessaires pour les corrections.

Usage:
    python apply_corrections.py
"""

import os
import sys
import subprocess
from pathlib import Path

# Couleurs pour le terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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
    """Execute une commande et affiche le résultat."""
    print_info(f"{description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print_success(f"{description} - Succès")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"{description} - Échec")
        if e.stderr:
            print(e.stderr)
        return False

def main():
    print_header("🔧 SCRIPT D'APPLICATION DES CORRECTIONS - DIGIT-HAB CRM")
    
    # Vérifier qu'on est dans le bon répertoire
    if not Path("manage.py").exists():
        print_error("Erreur: manage.py introuvable. Exécutez ce script depuis Django/")
        sys.exit(1)
    
    print_info("Ce script va:")
    print("  1. Créer les migrations pour PropertyVisit (models modifiés)")
    print("  2. Créer les migrations pour Favorites (nouvelle app)")
    print("  3. Appliquer toutes les migrations")
    print("  4. Vérifier l'état des migrations")
    
    response = input(f"\n{Colors.BOLD}Continuer? (y/N): {Colors.ENDC}")
    if response.lower() != 'y':
        print_warning("Opération annulée par l'utilisateur")
        sys.exit(0)
    
    # Étape 1: Backup de la base de données (SQLite)
    print_header("📦 ÉTAPE 1: Backup de la base de données")
    db_file = Path("digit_hab_crm/db.sqlite3")
    if db_file.exists():
        backup_file = Path("digit_hab_crm/db.sqlite3.backup")
        try:
            import shutil
            shutil.copy2(db_file, backup_file)
            print_success(f"Backup créé: {backup_file}")
        except Exception as e:
            print_warning(f"Impossible de créer le backup: {e}")
            response = input(f"{Colors.WARNING}Continuer sans backup? (y/N): {Colors.ENDC}")
            if response.lower() != 'y':
                sys.exit(1)
    else:
        print_info("Aucune base de données existante (nouveau projet)")
    
    # Étape 2: Créer les migrations pour properties
    print_header("📝 ÉTAPE 2: Créer les migrations - Properties")
    if not run_command(
        "python manage.py makemigrations properties",
        "Création des migrations properties"
    ):
        print_error("Échec de la création des migrations properties")
        sys.exit(1)
    
    # Étape 3: Créer les migrations pour favorites
    print_header("📝 ÉTAPE 3: Créer les migrations - Favorites")
    if not run_command(
        "python manage.py makemigrations favorites",
        "Création des migrations favorites"
    ):
        print_error("Échec de la création des migrations favorites")
        sys.exit(1)
    
    # Étape 4: Afficher les migrations à appliquer
    print_header("📋 ÉTAPE 4: Vérification des migrations")
    run_command(
        "python manage.py showmigrations",
        "Affichage des migrations"
    )
    
    # Étape 5: Appliquer les migrations
    print_header("⚙️ ÉTAPE 5: Application des migrations")
    print_warning("ATTENTION: Cette étape va modifier la base de données")
    response = input(f"{Colors.BOLD}Appliquer les migrations? (y/N): {Colors.ENDC}")
    if response.lower() != 'y':
        print_warning("Migrations créées mais non appliquées")
        print_info("Pour appliquer plus tard: python manage.py migrate")
        sys.exit(0)
    
    if not run_command(
        "python manage.py migrate",
        "Application des migrations"
    ):
        print_error("Échec de l'application des migrations")
        print_warning(f"Vous pouvez restaurer le backup: {backup_file}")
        sys.exit(1)
    
    # Étape 6: Vérifications finales
    print_header("✅ ÉTAPE 6: Vérifications finales")
    
    # Vérifier que favorites est bien installé
    if run_command(
        "python manage.py check",
        "Vérification du projet Django"
    ):
        print_success("Toutes les vérifications ont réussi")
    
    # Résumé
    print_header("📊 RÉSUMÉ DES CORRECTIONS APPLIQUÉES")
    print_success("✓ PropertyVisit model corrigé (champ client ajouté)")
    print_success("✓ scheduled_date/scheduled_time fusionnés")
    print_success("✓ App Favorites créée et configurée")
    print_success("✓ Migrations créées et appliquées")
    
    print("\n" + "="*60)
    print(f"{Colors.OKGREEN}{Colors.BOLD}✨ Corrections appliquées avec succès !{Colors.ENDC}")
    print("="*60 + "\n")
    
    print_info("Prochaines étapes:")
    print("  1. Tester les endpoints: python manage.py runserver")
    print("  2. Créer un superuser si nécessaire: python manage.py createsuperuser")
    print("  3. Tester les favoris: curl http://localhost:8000/api/favorites/")
    print(f"  4. Lire la documentation: ../CORRECTIONS-APPLIQUEES.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Opération interrompue par l'utilisateur{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Erreur inattendue: {e}")
        sys.exit(1)

