#!/bin/bash
# ════════════════════════════════════════════════════════
# Déploiement Final - DIGIT-HAB CRM
# Configuration PostgreSQL + Tests Complets
# ════════════════════════════════════════════════════════

set -e

echo "════════════════════════════════════════════════════════"
echo "  🚀 Déploiement Final - DIGIT-HAB CRM"
echo "════════════════════════════════════════════════════════"
echo ""

cd /var/www/digit-hab-crm

# ════════════════════════════════════════════════════════
# 1. Vérification de la Configuration
# ════════════════════════════════════════════════════════

echo "📋 Vérification de la configuration..."

if [ ! -f ".env" ]; then
    echo "❌ Fichier .env manquant !"
    echo "   Créez-le avec les bonnes valeurs PostgreSQL"
    exit 1
fi

echo "✅ Fichier .env présent"

# ════════════════════════════════════════════════════════
# 2. Arrêt et Nettoyage
# ════════════════════════════════════════════════════════

echo ""
echo "🛑 Arrêt des services..."
docker compose -f docker-compose.prod.yml down -v

echo "✅ Services arrêtés et volumes nettoyés"

# ════════════════════════════════════════════════════════
# 3. Rebuild Complet
# ════════════════════════════════════════════════════════

echo ""
echo "🔨 Rebuild des images..."
docker compose -f docker-compose.prod.yml build --no-cache

echo "✅ Images reconstruites"

# ════════════════════════════════════════════════════════
# 4. Démarrage des Services
# ════════════════════════════════════════════════════════

echo ""
echo "🚀 Démarrage des services..."
docker compose -f docker-compose.prod.yml up -d

echo "⏳ Attente du démarrage de PostgreSQL (30 secondes)..."
sleep 30

# ════════════════════════════════════════════════════════
# 5. Vérification de la Configuration Django
# ════════════════════════════════════════════════════════

echo ""
echo "🔍 Vérification de la configuration Django..."

docker compose -f docker-compose.prod.yml exec -T web python manage.py shell <<'VERIFY_EOF'
from django.conf import settings
print("=" * 60)
print("CONFIGURATION DJANGO")
print("=" * 60)
print(f"DEBUG: {settings.DEBUG}")
db_engine = settings.DATABASES['default']['ENGINE']
db_name = settings.DATABASES['default']['NAME']
db_host = settings.DATABASES['default']['HOST']
print(f"DB Engine: {db_engine}")
print(f"DB Name: {db_name}")
print(f"DB Host: {db_host}")
print("=" * 60)

if 'sqlite' in db_engine.lower():
    print("❌ ERREUR : Django utilise encore SQLite !")
    print("   Vérifiez que prod.py utilise PostgreSQL")
    import sys
    sys.exit(1)
else:
    print("✅ PostgreSQL configuré correctement")
VERIFY_EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Problème de configuration détecté !"
    echo "   Vérifiez que prod.py utilise PostgreSQL (pas SQLite)"
    exit 1
fi

# ════════════════════════════════════════════════════════
# 6. Migrations de la Base de Données
# ════════════════════════════════════════════════════════

echo ""
echo "🗄️  Application des migrations..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate

echo "✅ Migrations appliquées"

# ════════════════════════════════════════════════════════
# 7. Collecte des Fichiers Statiques
# ════════════════════════════════════════════════════════

echo ""
echo "📦 Collecte des fichiers statiques..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo "✅ Statiques collectés"

# ════════════════════════════════════════════════════════
# 8. Vérification des Tables
# ════════════════════════════════════════════════════════

echo ""
echo "📊 Vérification des tables PostgreSQL..."

docker compose -f docker-compose.prod.yml exec db psql -U ${DB_USER:-digit_hab_crm_user} -d ${DB_NAME:-digit_hab_crm_prod} -c "\dt" | head -15

# ════════════════════════════════════════════════════════
# 9. État des Services
# ════════════════════════════════════════════════════════

echo ""
echo "📊 État des services:"
docker compose -f docker-compose.prod.yml ps

# ════════════════════════════════════════════════════════
# 10. Tests des Endpoints
# ════════════════════════════════════════════════════════

echo ""
echo "🧪 Tests des endpoints..."
echo ""

test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    local code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$code" = "$expected" ] || [ "$code" = "200" ]; then
        echo "✅ $name: HTTP $code"
    else
        echo "❌ $name: HTTP $code (attendu: $expected)"
    fi
}

test_endpoint "Health Check    " "http://localhost:8001/health/" "200"
test_endpoint "Admin (redirect)" "https://api.digit-hab.altoppe.sn/admin/" "302"
test_endpoint "API Docs        " "https://api.digit-hab.altoppe.sn/api/docs/" "200"
test_endpoint "Properties      " "https://api.digit-hab.altoppe.sn/api/properties/" "200"
test_endpoint "Categories      " "https://api.digit-hab.altoppe.sn/api/properties/categories/" "200"

# ════════════════════════════════════════════════════════
# 11. Logs Récents
# ════════════════════════════════════════════════════════

echo ""
echo "📋 Logs récents (20 dernières lignes):"
docker compose -f docker-compose.prod.yml logs web --tail=20 | grep -v "Warning:" | tail -10

# ════════════════════════════════════════════════════════
# TERMINÉ
# ════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Déploiement Terminé !"
echo "════════════════════════════════════════════════════════"
echo ""
echo "🌐 URLs à tester dans le navigateur:"
echo "   - Admin: https://api.digit-hab.altoppe.sn/admin/"
echo "   - API Docs: https://api.digit-hab.altoppe.sn/api/docs/"
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Créer un superuser:"
echo "      docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
echo ""
echo "   2. Tester l'application mobile"
echo ""
echo "   3. Ajouter des données de test si nécessaire"
echo ""
echo "✨ DIGIT-HAB CRM est maintenant déployé ! 🎉"
