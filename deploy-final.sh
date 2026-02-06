#!/bin/bash

set -e  # Arrêter en cas d'erreur

echo "════════════════════════════════════════════════════════"
echo "  🚀 Déploiement DIGIT-HAB CRM Production"
echo "════════════════════════════════════════════════════════"
echo ""

# Variables de configuration
PROJECT_DIR="/var/www/digit-hab-crm"
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="/var/backups/digit-hab-crm"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "📍 Configuration du déploiement:"
echo "   - Répertoire: $PROJECT_DIR"
echo "   - Timestamp: $TIMESTAMP"
echo ""

# Créer le répertoire de backup si nécessaire
mkdir -p $BACKUP_DIR

# Étape 1: Naviguer vers le répertoire du projet
echo "📂 Navigation vers le répertoire du projet..."
cd $PROJECT_DIR

# Étape 2: Sauvegarder la base de données avant le déploiement
echo "💾 Sauvegarde de la base de données..."
docker compose -f $COMPOSE_FILE exec -T db pg_dump -U postgres digit_hab_crm > $BACKUP_DIR/db_backup_$TIMESTAMP.sql || true
echo "   ✅ Backup créé: $BACKUP_DIR/db_backup_$TIMESTAMP.sql"

# Étape 3: Pull les dernières modifications
echo "🔄 Récupération des dernières modifications..."
git fetch origin
git reset --hard origin/main
echo "   ✅ Code mis à jour"

# Étape 4: Vérifier les changements
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "   📌 Commit actuel: $CURRENT_COMMIT"

# Étape 5: Build des nouvelles images Docker
echo "🔨 Build des images Docker..."
docker compose -f $COMPOSE_FILE build --no-cache

# Étape 6: Arrêter les anciens conteneurs (sans supprimer les volumes)
echo "🛑 Arrêt des services existants..."
docker compose -f $COMPOSE_FILE down --remove-orphans

# Étape 7: Démarrer les nouveaux conteneurs
echo "▶️  Démarrage des nouveaux conteneurs..."
docker compose -f $COMPOSE_FILE up -d

# Étape 8: Attendre que la base de données soit prête
echo "⏳ Attente de la base de données..."
sleep 15

# Vérifier que le conteneur web est en cours d'exécution
if ! docker compose -f $COMPOSE_FILE ps | grep -q "web.*Up"; then
    echo "❌ Le conteneur web n'a pas démarré correctement!"
    docker compose -f $COMPOSE_FILE logs web
    exit 1
fi

# Étape 9: Appliquer les migrations
echo "🗄️  Application des migrations de base de données..."
docker compose -f $COMPOSE_FILE exec -T web python manage.py migrate --noinput

# Étape 10: Collecter les fichiers statiques
echo "📦 Collecte des fichiers statiques..."
docker compose -f $COMPOSE_FILE exec -T web python manage.py collectstatic --noinput

# Étape 11: Redémarrer les services pour appliquer tous les changements
echo "🔄 Redémarrage des services..."
docker compose -f $COMPOSE_FILE restart web

# Étape 12: Nettoyer les anciennes images Docker
echo "🧹 Nettoyage des anciennes images..."
docker image prune -f

# Étape 13: Nettoyer les anciens backups (garder les 10 derniers)
echo "🗑️  Nettoyage des anciens backups..."
cd $BACKUP_DIR
ls -t db_backup_*.sql | tail -n +11 | xargs -r rm
cd $PROJECT_DIR

# Étape 14: Vérifier l'état des services
echo ""
echo "🎯 État des services:"
docker compose -f $COMPOSE_FILE ps

# Étape 15: Vérifier la santé de l'application
echo ""
echo "🏥 Test de santé de l'application..."
sleep 5

if docker compose -f $COMPOSE_FILE exec -T web python manage.py check --deploy > /dev/null 2>&1; then
    echo "   ✅ Application en bonne santé"
else
    echo "   ⚠️  Avertissements détectés (vérifier les logs)"
fi

# Afficher les derniers logs
echo ""
echo "📋 Derniers logs de l'application:"
docker compose -f $COMPOSE_FILE logs --tail=20 web

# Résumé final
echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Déploiement terminé avec succès !"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📊 Informations de déploiement:"
echo "   - Commit: $CURRENT_COMMIT"
echo "   - Date: $TIMESTAMP"
echo "   - Backup DB: $BACKUP_DIR/db_backup_$TIMESTAMP.sql"
echo ""
echo "🌐 URLs à tester:"
echo "   - Admin: https://api.digit-hab.altoppe.sn/admin/"
echo "   - API: https://api.digit-hab.altoppe.sn/api/"
echo "   - Docs: https://api.digit-hab.altoppe.sn/api/docs/"
echo ""
echo "📝 Commandes utiles:"
echo "   - Voir les logs: docker compose -f $COMPOSE_FILE logs -f web"
echo "   - Redémarrer: docker compose -f $COMPOSE_FILE restart"
echo "   - Arrêter: docker compose -f $COMPOSE_FILE stop"
echo ""
echo "✨ Déploiement réussi !"
