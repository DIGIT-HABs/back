#!/bin/bash
# ════════════════════════════════════════════════════════
# Fix Gunicorn - Installation et Redémarrage
# À exécuter SUR LE VPS
# ════════════════════════════════════════════════════════

set -e

echo "🔧 Installation de Gunicorn..."
echo ""

cd /var/www/digit-hab-crm
git pull
# 1. Arrêter les services
echo "🛑 Arrêt des services..."
docker compose -f docker-compose.prod.yml down

# 2. Rebuild avec le nouveau requirements.txt
echo "🔨 Rebuild avec Gunicorn..."
docker compose -f docker-compose.prod.yml build --no-cache web

# 3. Redémarrer tous les services
echo "🚀 Démarrage des services..."
docker compose -f docker-compose.prod.yml up -d

# 4. Attendre 30 secondes
echo "⏳ Attente du démarrage (30 secondes)..."
sleep 30

# 5. Vérifier l'état
echo ""
echo "📊 État des services:"
docker compose -f docker-compose.prod.yml ps

# 6. Vérifier les logs
echo ""
echo "📋 Logs du service web (20 dernières lignes):"
docker compose -f docker-compose.prod.yml logs web --tail=20

# 7. Test de l'endpoint
echo ""
echo "🧪 Test de l'endpoint health:"
curl -I http://localhost:8001/health/ 2>&1 | grep "HTTP" || echo "   ⚠️  Service pas encore prêt"

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Fix Terminé !"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Si le service tourne correctement, exécutez:"
echo ""
echo "  # Migrations"
echo "  docker compose -f docker-compose.prod.yml exec web python manage.py migrate"
echo ""
echo "  # Collecte des statiques"
echo "  docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput"
echo ""
echo "  # Créer un superuser"
echo "  docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
echo ""
echo "  # Test HTTPS"
echo "  curl -I https://api.digit-hab.altoppe.sn/health/"
echo ""
