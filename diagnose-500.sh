#!/bin/bash
# ════════════════════════════════════════════════════════
# Diagnostic des Erreurs 500
# ════════════════════════════════════════════════════════

echo "🔍 Diagnostic des erreurs 500..."
echo ""

cd /var/www/digit-hab-crm

# 1. État des services
echo "1️⃣  État des services:"
docker compose -f docker-compose.prod.yml ps
echo ""

# 2. Logs récents du service web
echo "2️⃣  Logs récents (50 dernières lignes):"
docker compose -f docker-compose.prod.yml logs web --tail=50
echo ""

# 3. Test de connexion à la DB
echo "3️⃣  Test de connexion à la base de données:"
docker compose -f docker-compose.prod.yml exec -T web python manage.py dbshell --command="SELECT 1;" 2>&1 || echo "   ❌ Connexion DB échouée"
echo ""

# 4. Vérifier les migrations
echo "4️⃣  État des migrations:"
docker compose -f docker-compose.prod.yml exec -T web python manage.py showmigrations 2>&1 | head -30
echo ""

# 5. Test d'import des modèles
echo "5️⃣  Test d'import des modèles:"
docker compose -f docker-compose.prod.yml exec -T web python -c "
from apps.properties.models import Property, PropertyCategory
print('✅ Modèles importés avec succès')
" 2>&1 || echo "   ❌ Erreur d'import"
echo ""

# 6. Vérifier les variables d'environnement
echo "6️⃣  Variables d'environnement (DB):"
docker compose -f docker-compose.prod.yml exec -T web env | grep -E "DB_|DJANGO_SETTINGS_MODULE" | grep -v PASSWORD
echo ""

# 7. Test de l'endpoint depuis le conteneur
echo "7️⃣  Test de l'endpoint depuis le conteneur:"
docker compose -f docker-compose.prod.yml exec -T web curl -s http://localhost:8000/api/properties/categories/ | head -20
echo ""

echo "════════════════════════════════════════════════════════"
echo "📋 Résumé"
echo "════════════════════════════════════════════════════════"
echo "Si vous voyez des erreurs ci-dessus, envoyez-les moi"
echo "pour que je puisse vous aider à les corriger."
echo ""
