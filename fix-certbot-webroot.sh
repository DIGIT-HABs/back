#!/bin/bash
# ════════════════════════════════════════════════════════
# Fix Certbot Webroot - Corriger l'accès au dossier certbot
# ════════════════════════════════════════════════════════

set -e

echo "🔧 Correction du problème Certbot Webroot..."
echo ""

# ════════════════════════════════════════════════════════
# 1. Vérifier et recréer le dossier certbot
# ════════════════════════════════════════════════════════

echo "📁 Préparation du dossier certbot..."
sudo mkdir -p /var/www/certbot/.well-known/acme-challenge
sudo chmod -R 755 /var/www/certbot
sudo chown -R www-data:www-data /var/www/certbot

# Créer un fichier de test
echo "OK" > /var/www/certbot/.well-known/acme-challenge/test.txt
chmod 644 /var/www/certbot/.well-known/acme-challenge/test.txt

echo "✅ Dossier certbot créé"

# ════════════════════════════════════════════════════════
# 2. Vérifier le docker-compose d'AL-TOPPE
# ════════════════════════════════════════════════════════

echo ""
echo "🐳 Vérification docker-compose.prod.yml d'AL-TOPPE..."
cd /var/www/al-toppe

# Vérifier si le volume certbot est monté
if grep -q "/var/www/certbot:/var/www/certbot" docker-compose.prod.yml; then
    echo "✅ Volume certbot déjà configuré"
else
    echo "⚠️  Volume certbot manquant, ajout en cours..."
    
    # Backup
    cp docker-compose.prod.yml docker-compose.prod.yml.backup.certbot.$(date +%Y%m%d_%H%M%S)
    
    # Ajouter le volume manuellement
    # On va ajouter juste avant "depends_on:" du service nginx
    sed -i '/nginx:/,/depends_on:/ {
        /depends_on:/i\    volumes:\n      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro\n      - ./staticfiles:/var/www/al-toppe/staticfiles:ro\n      - ./media:/var/www/al-toppe/media:ro\n      - ./ssl:/etc/nginx/ssl:ro\n      - /var/www/certbot:/var/www/certbot:ro\n      - /etc/letsencrypt:/etc/letsencrypt:ro
    }' docker-compose.prod.yml 2>/dev/null || {
        echo "❌ Impossible de modifier automatiquement docker-compose.prod.yml"
        echo ""
        echo "Veuillez ajouter manuellement ces volumes au service nginx :"
        echo ""
        cat <<'EOF'
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./staticfiles:/var/www/al-toppe/staticfiles:ro
      - ./media:/var/www/al-toppe/media:ro
      - ./ssl:/etc/nginx/ssl:ro
      - /var/www/certbot:/var/www/certbot:ro        # ✅ AJOUTER CETTE LIGNE
      - /etc/letsencrypt:/etc/letsencrypt:ro         # ✅ AJOUTER CETTE LIGNE
    depends_on:
      - web
    networks:
      - app-network
    restart: unless-stopped
EOF
        echo ""
        read -p "Appuyez sur Entrée quand c'est fait..."
    }
fi

# ════════════════════════════════════════════════════════
# 3. Redémarrer Nginx d'AL-TOPPE
# ════════════════════════════════════════════════════════

echo ""
echo "🔄 Redémarrage de Nginx d'AL-TOPPE..."
docker compose -f docker-compose.prod.yml down nginx
docker compose -f docker-compose.prod.yml up -d nginx
sleep 3

# Vérifier que Nginx tourne
if ! docker ps | grep -q "al-toppe-nginx"; then
    echo "❌ Erreur : Nginx ne démarre pas"
    docker compose -f docker-compose.prod.yml logs nginx
    exit 1
fi

echo "✅ Nginx redémarré"

# ════════════════════════════════════════════════════════
# 4. Tester l'accès au webroot
# ════════════════════════════════════════════════════════

echo ""
echo "🧪 Test de l'accès au webroot..."

# Test depuis le conteneur
echo "  Test interne (depuis le conteneur):"
docker compose -f docker-compose.prod.yml exec nginx ls -la /var/www/certbot/.well-known/acme-challenge/ || {
    echo "  ❌ Le dossier n'est pas accessible depuis le conteneur"
    exit 1
}

# Test depuis l'extérieur
echo ""
echo "  Test externe (HTTP):"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://digit-hab.altoppe.sn/.well-known/acme-challenge/test.txt)

if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✅ HTTP 200 - Webroot accessible !"
else
    echo "  ⚠️  HTTP $HTTP_CODE - Vérifier la config Nginx"
    echo ""
    echo "  Contenu de nginx.prod.conf (server block HTTP):"
    grep -A 10 "listen 80" /var/www/al-toppe/nginx.prod.conf | head -15
fi

# ════════════════════════════════════════════════════════
# 5. Réessayer Certbot
# ════════════════════════════════════════════════════════

echo ""
echo "🔒 Tentative d'obtention des certificats SSL..."

# Nettoyer les éventuelles tentatives précédentes
sudo rm -rf /var/www/certbot/.well-known/acme-challenge/*

# Obtenir les certificats
sudo certbot certonly --webroot \
    -w /var/www/certbot \
    -d digit-hab.altoppe.sn \
    -d api.digit-hab.altoppe.sn \
    --email souleymane9700@gmail.com \
    --agree-tos \
    --non-interactive \
    --verbose

# Vérifier le résultat
if [ -d "/etc/letsencrypt/live/digit-hab.altoppe.sn" ]; then
    echo ""
    echo "✅ Certificats SSL obtenus avec succès !"
    sudo ls -la /etc/letsencrypt/live/digit-hab.altoppe.sn/
    
    # ════════════════════════════════════════════════════════
    # 6. Mettre à jour la config Nginx avec SSL
    # ════════════════════════════════════════════════════════
    
    echo ""
    echo "🔧 Mise à jour de la config Nginx avec SSL DIGIT-HAB..."
    
    if [ -f "/var/www/digit-hab-crm/nginx.prod.multi-projects.conf" ]; then
        cp /var/www/digit-hab-crm/nginx.prod.multi-projects.conf /var/www/al-toppe/nginx.prod.conf
        echo "✅ Configuration complète installée"
    else
        echo "⚠️  Fichier nginx.prod.multi-projects.conf non trouvé"
        echo "   Vous devrez ajouter manuellement le server block DIGIT-HAB"
    fi
    
    # Redémarrer Nginx
    echo "🔄 Redémarrage final de Nginx..."
    docker compose -f /var/www/al-toppe/docker-compose.prod.yml restart nginx
    sleep 3
    
    echo "✅ Configuration terminée !"
else
    echo ""
    echo "❌ Échec de l'obtention des certificats"
    echo "   Consultez les logs : /var/log/letsencrypt/letsencrypt.log"
    exit 1
fi

# ════════════════════════════════════════════════════════
# 7. Tests finaux
# ════════════════════════════════════════════════════════

echo ""
echo "🧪 Tests finaux..."
echo "  - Test HTTP -> HTTPS redirect:"
curl -I http://digit-hab.altoppe.sn/ 2>&1 | grep -E "HTTP|Location" | head -2

echo ""
echo "  - Test HTTPS (devrait fonctionner après déploiement de DIGIT-HAB):"
curl -I https://api.digit-hab.altoppe.sn/health/ 2>&1 | grep "HTTP" || echo "    (Normal si DIGIT-HAB n'est pas encore déployé)"

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Correction Terminée !"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📝 Prochaine étape : Déployer DIGIT-HAB CRM"
echo "   cd /var/www/digit-hab-crm"
echo "   docker compose -f docker-compose.prod.yml up -d --build"
echo ""
