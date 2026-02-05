#!/bin/bash
# ════════════════════════════════════════════════════════
# Fix CSRF - Correction du problème 403 sur /admin/
# À exécuter SUR LE VPS après avoir transféré prod.py corrigé
# ════════════════════════════════════════════════════════

set -e

echo "🔧 Correction du problème CSRF..."
echo ""

cd /var/www/digit-hab-crm

# 1. Redémarrer le service web
echo "🔄 Redémarrage du service web..."
docker compose -f docker-compose.prod.yml restart web

# 2. Attendre que le service soit prêt
echo "⏳ Attente du redémarrage (15 secondes)..."
sleep 15

# 3. Vérifier l'état
echo ""
echo "📊 État du service web:"
docker compose -f docker-compose.prod.yml ps web

# 4. Vérifier les logs
echo ""
echo "📋 Logs récents:"
docker compose -f docker-compose.prod.yml logs web --tail=15

# 5. Test des endpoints
echo ""
echo "🧪 Tests:"

echo "  - Health check HTTP:"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health/)
echo "    Status: $HTTP_STATUS"

echo "  - Health check HTTPS:"
HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.digit-hab.altoppe.sn/health/)
echo "    Status: $HTTPS_STATUS"

echo "  - Admin page:"
ADMIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.digit-hab.altoppe.sn/admin/)
echo "    Status: $ADMIN_STATUS (devrait être 200 ou 302)"

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Correction Terminée !"
echo "════════════════════════════════════════════════════════"
echo ""
echo "🌐 Testez maintenant dans votre navigateur:"
echo "   - Admin: https://api.digit-hab.altoppe.sn/admin/"
echo "   - API Docs: https://api.digit-hab.altoppe.sn/api/docs/"
echo ""
echo "📝 Si l'admin fonctionne, créez un superuser:"
echo "   docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
echo ""
