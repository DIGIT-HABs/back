#!/bin/bash
# ════════════════════════════════════════════════════════
# Fix Profile Errors - Correction des erreurs "User has no profile"
# À exécuter SUR LE VPS après avoir transféré les fichiers corrigés
# ════════════════════════════════════════════════════════

set -e

echo "🔧 Correction des erreurs de profil utilisateur..."
echo ""

cd /var/www/digit-hab-crm

# 1. Créer les profils manquants pour tous les utilisateurs
echo "👤 Création des profils manquants..."
docker compose -f docker-compose.prod.yml exec -T web python << 'PYTHON_EOF'
from apps.custom_auth.models import User, UserProfile

# Créer un profil pour chaque utilisateur qui n'en a pas
users_without_profile = []
for user in User.objects.all():
    try:
        _ = user.profile
    except User.profile.RelatedObjectDoesNotExist:
        users_without_profile.append(user)
        # Créer un profil avec des valeurs par défaut
        UserProfile.objects.create(
            user=user,
            role=user.role,
            phone_number='',
            address=''
        )
        print(f"✅ Profil créé pour {user.username} ({user.email})")

if not users_without_profile:
    print("✅ Tous les utilisateurs ont déjà un profil")
else:
    print(f"\n✅ {len(users_without_profile)} profils créés")
PYTHON_EOF

# 2. Redémarrer le service web
echo ""
echo "🔄 Redémarrage du service web..."
docker compose -f docker-compose.prod.yml restart web

# 3. Attendre que le service soit prêt
echo "⏳ Attente du redémarrage (15 secondes)..."
sleep 15

# 4. Vérifier l'état
echo ""
echo "📊 État du service web:"
docker compose -f docker-compose.prod.yml ps web

# 5. Tests des endpoints
echo ""
echo "🧪 Tests des endpoints:"

echo "  - Health check:"
curl -s -o /dev/null -w "    HTTP %{http_code}\n" http://localhost:8001/health/

echo "  - Properties:"
curl -s -o /dev/null -w "    HTTP %{http_code}\n" http://localhost:8001/api/properties/

echo "  - Properties categories:"
curl -s -o /dev/null -w "    HTTP %{http_code}\n" http://localhost:8001/api/properties/categories/

echo "  - Reservations stats (nécessite authentification):"
curl -s -o /dev/null -w "    HTTP %{http_code}\n" http://localhost:8001/api/reservations/stats/

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Correction Terminée !"
echo "════════════════════════════════════════════════════════"
echo ""
echo "🌐 Testez maintenant dans l'application mobile:"
echo "   Tous les endpoints devraient fonctionner"
echo ""
echo "Si vous voyez encore des erreurs, vérifiez les logs:"
echo "   docker compose -f docker-compose.prod.yml logs web --tail=50"
echo ""
