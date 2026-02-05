#!/bin/bash
# ════════════════════════════════════════════════════════
# Script de Mise à Jour Rapide sur le VPS
# À exécuter SUR LE VPS après avoir transféré les fichiers corrigés
# ════════════════════════════════════════════════════════

set -e

echo "════════════════════════════════════════════════════════"
echo "  Mise à Jour DIGIT-HAB CRM"
echo "════════════════════════════════════════════════════════"
echo ""

cd /var/www/digit-hab-crm

# 1. Arrêter les services
echo "🛑 Arrêt des services..."
docker compose -f docker-compose.prod.yml down

# 2. Rebuild les images
echo "🔨 Rebuild des images..."
docker compose -f docker-compose.prod.yml build --no-cache

# 3. Redémarrer
echo "🚀 Démarrage des services..."
docker compose -f docker-compose.prod.yml up -d

# 4. Attendre que les services soient prêts
echo "⏳ Attente du démarrage (30 secondes)..."
sleep 30

# 5. Vérifier l'état
echo ""
echo "📊 État des services:"
docker compose -f docker-compose.prod.yml ps

# 6. Migrations
echo ""
echo "🗄️  Migrations de la base de données..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# 7. Collecte des statiques
echo ""
echo "📦 Collecte des fichiers statiques..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# 8. Tests
echo ""
echo "🧪 Tests des endpoints..."
echo "  - Health check local (port 8001):"
curl -I http://localhost:8001/health/ 2>&1 | grep "HTTP" || echo "    ⚠️  Endpoint non accessible"

echo ""
echo "  - Health check HTTPS:"
curl -I https://api.digit-hab.altoppe.sn/health/ 2>&1 | grep "HTTP" || echo "    ⚠️  Endpoint non accessible"

# 9. Logs
echo ""
echo "📋 Logs récents (web):"
docker compose -f docker-compose.prod.yml logs web --tail=20

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Mise à Jour Terminée !"
echo "════════════════════════════════════════════════════════"
echo ""
echo "🌐 URLs à tester:"
echo "   - Admin: https://api.digit-hab.altoppe.sn/admin/"
echo "   - API Docs: https://api.digit-hab.altoppe.sn/api/docs/"
echo "   - Health: https://api.digit-hab.altoppe.sn/health/"
echo ""
echo "📝 Pour créer un superuser:"
echo "   docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
echo ""
