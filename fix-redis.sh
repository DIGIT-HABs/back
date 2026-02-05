#!/bin/bash
# ════════════════════════════════════════════════════════
# Fix Redis Configuration - Correction des erreurs 500
# À exécuter SUR LE VPS après avoir transféré base.py corrigé
# ════════════════════════════════════════════════════════

set -e

echo "🔧 Correction de la configuration Redis..."
echo ""

cd /var/www/digit-hab-crm

# 1. Redémarrer tous les services
echo "🔄 Redémarrage de tous les services..."
docker compose -f docker-compose.prod.yml restart

# 2. Attendre que les services soient prêts
echo "⏳ Attente du redémarrage (20 secondes)..."
sleep 20

# 3. Vérifier l'état
echo ""
echo "📊 État des services:"
docker compose -f docker-compose.prod.yml ps

# 4. Vérifier les logs
echo ""
echo "📋 Logs du service web (20 dernières lignes):"
docker compose -f docker-compose.prod.yml logs web --tail=20

# 5. Tests des endpoints
echo ""
echo "🧪 Tests des endpoints:"

echo "  - Health check:"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health/)
echo "    HTTP Status: $HTTP_STATUS"

echo "  - Properties categories:"
PROPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/properties/categories/)
echo "    HTTP Status: $PROPS_STATUS"

echo "  - Properties list:"
PROPS_LIST_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/properties/)
echo "    HTTP Status: $PROPS_LIST_STATUS"

# 6. Test avec authentification (si vous avez un token)
echo ""
echo "  - Test avec authentification (si vous avez un token, ajoutez-le dans le script)"

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Correction Terminée !"
echo "════════════════════════════════════════════════════════"
echo ""
echo "🌐 Testez maintenant dans l'application mobile:"
echo "   - Login devrait fonctionner"
echo "   - Les endpoints /api/properties/ devraient retourner 200"
echo "   - Les endpoints /api/properties/categories/ devraient retourner 200"
echo ""
echo "Si vous voyez encore des erreurs 500, exécutez:"
echo "   docker compose -f docker-compose.prod.yml logs web --tail=50"
echo ""
