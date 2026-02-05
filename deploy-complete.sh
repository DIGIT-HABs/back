#!/bin/bash

# ════════════════════════════════════════════════════════
# Script de Déploiement Complet - DIGIT-HAB CRM avec AL-TOPPE
# ════════════════════════════════════════════════════════

set -e  # Arrêter en cas d'erreur

echo "════════════════════════════════════════════════════════"
echo "  Déploiement DIGIT-HAB CRM avec AL-TOPPE"
echo "  Configuration Multi-Projets"
echo "════════════════════════════════════════════════════════"
echo ""

# ════════════════════════════════════════════════════════
# VARIABLES
# ════════════════════════════════════════════════════════

ALTOPPE_DIR="/var/www/al-toppe"
DIGITHAB_DIR="/var/www/digit-hab-crm"
DOMAIN1="digit-hab.altoppe.sn"
DOMAIN2="api.digit-hab.altoppe.sn"
EMAIL="souleymane9700@gmail.com"

echo "📍 Configuration:"
echo "   - AL-TOPPE: $ALTOPPE_DIR"
echo "   - DIGIT-HAB: $DIGITHAB_DIR"
echo "   - Domaines: $DOMAIN1, $DOMAIN2"
echo ""

# ════════════════════════════════════════════════════════
# ÉTAPE 1 : Vérification DNS
# ════════════════════════════════════════════════════════

echo "🔍 Vérification DNS..."
DNS_OK=true

if ! nslookup $DOMAIN1 > /dev/null 2>&1; then
    echo "❌ $DOMAIN1 ne résout pas !"
    DNS_OK=false
fi

if ! nslookup $DOMAIN2 > /dev/null 2>&1; then
    echo "❌ $DOMAIN2 ne résout pas !"
    DNS_OK=false
fi

if [ "$DNS_OK" = false ]; then
    echo ""
    echo "⚠️  Les DNS ne sont pas configurés correctement !"
    echo "   Ajoutez ces enregistrements DNS :"
    echo ""
    echo "   Type    Nom              Valeur              TTL"
    echo "   ────────────────────────────────────────────────"
    echo "   A       digit-hab        72.60.189.237       3600"
    echo "   AAAA    digit-hab        2a02:4780:28:d4f7::1  3600"
    echo "   A       api.digit-hab    72.60.189.237       3600"
    echo "   AAAA    api.digit-hab    2a02:4780:28:d4f7::1  3600"
    echo ""
    read -p "DNS configurés ? Continuer quand même ? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ DNS OK"
fi

# ════════════════════════════════════════════════════════
# ÉTAPE 2 : Préparation des Dossiers
# ════════════════════════════════════════════════════════

echo ""
echo "📁 Préparation des dossiers..."

# Créer le dossier certbot
sudo mkdir -p /var/www/certbot
sudo chown -R $USER:$USER /var/www/certbot

# Créer les dossiers static/media pour digit-hab
sudo mkdir -p $DIGITHAB_DIR/staticfiles
sudo mkdir -p $DIGITHAB_DIR/media
sudo chown -R $USER:$USER $DIGITHAB_DIR/staticfiles
sudo chown -R $USER:$USER $DIGITHAB_DIR/media

echo "✅ Dossiers créés"

# ════════════════════════════════════════════════════════
# ÉTAPE 3 : Backup et Mise à Jour Config Nginx d'AL-TOPPE
# ════════════════════════════════════════════════════════

echo ""
echo "🔧 Mise à jour de la configuration Nginx..."

# Backup de la config actuelle
cd $ALTOPPE_DIR
cp nginx.prod.conf nginx.prod.conf.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Backup de nginx.prod.conf créé"

# Vérifier si la nouvelle config existe
if [ ! -f "$DIGITHAB_DIR/nginx.prod.multi-projects.conf" ]; then
    echo "❌ Le fichier nginx.prod.multi-projects.conf n'existe pas dans $DIGITHAB_DIR"
    echo "   Copiez-le d'abord depuis votre machine locale !"
    exit 1
fi

# Copier la nouvelle config (sans les certificats SSL digit-hab pour l'instant)
# On va créer une version temporaire sans le bloc HTTPS digit-hab
cat > $ALTOPPE_DIR/nginx.prod.conf.temp <<'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;

    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=30r/m;

    upstream django_backend {
        server web:8000;
    }

    # HTTP avec webroot pour Certbot
    server {
        listen 80;
        server_name altoppe.sn www.altoppe.sn api.altoppe.sn digit-hab.altoppe.sn api.digit-hab.altoppe.sn;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 301 https://$server_name$request_uri;
        }
    }

    # AL-TOPPE HTTPS (configuration existante)
    server {
        listen 443 ssl;
        server_name api.altoppe.sn;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        client_max_body_size 20M;

        location /static/ {
            alias /var/www/al-toppe/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        location /media/ {
            alias /var/www/al-toppe/media/;
            expires 30d;
            add_header Cache-Control "public";
        }

        location /api/auth/login/ {
            limit_req zone=login burst=20 nodelay;
            proxy_pass http://django_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        location /api/ {
            limit_req zone=api burst=80 nodelay;
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' "$http_origin";
                add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, PATCH, DELETE, OPTIONS';
                add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, X-CSRFToken, X-Requested-With';
                add_header 'Access-Control-Allow-Credentials' 'true';
                add_header 'Access-Control-Max-Age' 86400;
                add_header 'Content-Length' 0;
                add_header 'Content-Type' 'text/plain; charset=utf-8';
                return 204;
            }
            proxy_pass http://django_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        location /admin/ {
            proxy_pass http://django_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/docs/ {
            proxy_pass http://django_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health/ {
            proxy_pass http://django_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            access_log off;
        }

        location = / {
            return 301 /api/docs/;
        }

        location / {
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' "$http_origin";
                add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, PATCH, DELETE, OPTIONS';
                add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type, X-CSRFToken, X-Requested-With';
                add_header 'Access-Control-Allow-Credentials' 'true';
                add_header 'Access-Control-Max-Age' 86400;
                add_header 'Content-Length' 0;
                add_header 'Content-Type' 'text/plain; charset=utf-8';
                return 204;
            }
            proxy_pass http://django_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

mv $ALTOPPE_DIR/nginx.prod.conf.temp $ALTOPPE_DIR/nginx.prod.conf
echo "✅ Configuration Nginx mise à jour (étape 1 - sans SSL digit-hab)"

# ════════════════════════════════════════════════════════
# ÉTAPE 4 : Mise à Jour docker-compose d'AL-TOPPE
# ════════════════════════════════════════════════════════

echo ""
echo "🐳 Mise à jour docker-compose.prod.yml..."

# Backup
cp docker-compose.prod.yml docker-compose.prod.yml.backup.$(date +%Y%m%d_%H%M%S)

# Vérifier si les volumes sont déjà présents
if ! grep -q "/var/www/digit-hab-crm/staticfiles" docker-compose.prod.yml; then
    # Utiliser Python pour modifier le YAML proprement
    python3 << 'PYTHON_EOF'
import yaml
import sys

with open('docker-compose.prod.yml', 'r') as f:
    config = yaml.safe_load(f)

# Ajouter les volumes au service nginx
if 'services' in config and 'nginx' in config['services']:
    nginx = config['services']['nginx']
    
    # Ajouter les volumes s'ils n'existent pas
    new_volumes = [
        '/var/www/digit-hab-crm/staticfiles:/var/www/digit-hab-crm/staticfiles:ro',
        '/var/www/digit-hab-crm/media:/var/www/digit-hab-crm/media:ro',
        '/etc/letsencrypt:/etc/letsencrypt:ro',
        '/var/www/certbot:/var/www/certbot:ro'
    ]
    
    if 'volumes' not in nginx:
        nginx['volumes'] = []
    
    for vol in new_volumes:
        if vol not in nginx['volumes']:
            nginx['volumes'].append(vol)
    
    # Ajouter extra_hosts
    if 'extra_hosts' not in nginx:
        nginx['extra_hosts'] = ['host.docker.internal:host-gateway']

    with open('docker-compose.prod.yml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print("✅ docker-compose.prod.yml mis à jour")
else:
    print("❌ Service nginx non trouvé dans docker-compose.prod.yml")
    sys.exit(1)
PYTHON_EOF

    if [ $? -ne 0 ]; then
        echo "⚠️  Erreur Python YAML, modification manuelle requise"
        echo "   Ajoutez ces volumes au service nginx dans docker-compose.prod.yml :"
        echo "     - /var/www/digit-hab-crm/staticfiles:/var/www/digit-hab-crm/staticfiles:ro"
        echo "     - /var/www/digit-hab-crm/media:/var/www/digit-hab-crm/media:ro"
        echo "     - /etc/letsencrypt:/etc/letsencrypt:ro"
        echo "     - /var/www/certbot:/var/www/certbot:ro"
        echo "   Et ajoutez :"
        echo "     extra_hosts:"
        echo "       - \"host.docker.internal:host-gateway\""
        read -p "Continuer quand c'est fait ? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "✅ docker-compose.prod.yml déjà à jour"
fi

# ════════════════════════════════════════════════════════
# ÉTAPE 5 : Redémarrer Nginx d'AL-TOPPE
# ════════════════════════════════════════════════════════

echo ""
echo "🔄 Redémarrage du Nginx d'AL-TOPPE..."
docker compose -f docker-compose.prod.yml restart nginx
sleep 5

# Vérifier
if docker ps | grep -q "al-toppe-nginx"; then
    echo "✅ Nginx d'AL-TOPPE redémarré"
else
    echo "❌ Erreur lors du redémarrage de Nginx"
    docker compose -f docker-compose.prod.yml logs nginx
    exit 1
fi

# ════════════════════════════════════════════════════════
# ÉTAPE 6 : Obtenir les Certificats SSL pour DIGIT-HAB
# ════════════════════════════════════════════════════════

echo ""
echo "🔒 Obtention des certificats SSL pour DIGIT-HAB..."

# Vérifier si les certificats existent déjà
if [ -d "/etc/letsencrypt/live/$DOMAIN1" ]; then
    echo "⚠️  Les certificats existent déjà"
    read -p "Renouveler les certificats ? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo certbot certonly --webroot \
            -w /var/www/certbot \
            -d $DOMAIN1 \
            -d $DOMAIN2 \
            --email $EMAIL \
            --agree-tos \
            --force-renewal \
            --non-interactive
    fi
else
    sudo certbot certonly --webroot \
        -w /var/www/certbot \
        -d $DOMAIN1 \
        -d $DOMAIN2 \
        --email $EMAIL \
        --agree-tos \
        --non-interactive
fi

# Vérifier que les certificats ont été créés
if [ ! -d "/etc/letsencrypt/live/$DOMAIN1" ]; then
    echo "❌ Échec de création des certificats SSL"
    echo "   Vérifiez que les DNS pointent vers ce serveur !"
    exit 1
fi

echo "✅ Certificats SSL obtenus !"
sudo ls -la /etc/letsencrypt/live/$DOMAIN1/

# ════════════════════════════════════════════════════════
# ÉTAPE 7 : Mettre à Jour Nginx avec SSL DIGIT-HAB
# ════════════════════════════════════════════════════════

echo ""
echo "🔧 Mise à jour finale de Nginx avec SSL DIGIT-HAB..."

# Maintenant on peut copier la config complète
if [ -f "$DIGITHAB_DIR/nginx.prod.multi-projects.conf" ]; then
    cp $DIGITHAB_DIR/nginx.prod.multi-projects.conf $ALTOPPE_DIR/nginx.prod.conf
    echo "✅ Configuration Nginx complète installée"
else
    echo "⚠️  Fichier nginx.prod.multi-projects.conf non trouvé"
    echo "   Vous devrez l'ajouter manuellement"
fi

# Redémarrer Nginx
echo "🔄 Redémarrage final de Nginx..."
docker compose -f docker-compose.prod.yml restart nginx
sleep 5

# ════════════════════════════════════════════════════════
# ÉTAPE 8 : Déployer DIGIT-HAB CRM
# ════════════════════════════════════════════════════════

echo ""
echo "🚀 Déploiement de DIGIT-HAB CRM..."
cd $DIGITHAB_DIR

# Build les images
echo "🔨 Build des images Docker..."
docker compose -f docker-compose.prod.yml build --no-cache

# Démarrer les services
echo "▶️  Démarrage des services..."
docker compose -f docker-compose.prod.yml up -d

# Attendre que la DB soit prête
echo "⏳ Attente de la base de données..."
sleep 15

# Migrations
echo "🗄️  Application des migrations..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Collecte des statiques
echo "📦 Collecte des fichiers statiques..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# ════════════════════════════════════════════════════════
# ÉTAPE 9 : Vérifications Finales
# ════════════════════════════════════════════════════════

echo ""
echo "🔍 Vérifications finales..."

# Status des services
echo ""
echo "📊 Services AL-TOPPE:"
cd $ALTOPPE_DIR
docker compose -f docker-compose.prod.yml ps

echo ""
echo "📊 Services DIGIT-HAB:"
cd $DIGITHAB_DIR
docker compose -f docker-compose.prod.yml ps

# Test des endpoints
echo ""
echo "🧪 Test des endpoints..."

echo "  - AL-TOPPE: https://api.altoppe.sn/health/"
curl -s -o /dev/null -w "    Status: %{http_code}\n" https://api.altoppe.sn/health/ || echo "    ❌ Erreur"

echo "  - DIGIT-HAB: https://api.digit-hab.altoppe.sn/health/"
curl -s -o /dev/null -w "    Status: %{http_code}\n" https://api.digit-hab.altoppe.sn/health/ || echo "    ❌ Erreur"

# ════════════════════════════════════════════════════════
# TERMINÉ !
# ════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Déploiement Terminé !"
echo "════════════════════════════════════════════════════════"
echo ""
echo "🌐 URLs à Tester:"
echo ""
echo "   AL-TOPPE:"
echo "   - Admin: https://api.altoppe.sn/admin/"
echo "   - API Docs: https://api.altoppe.sn/api/docs/"
echo "   - Health: https://api.altoppe.sn/health/"
echo ""
echo "   DIGIT-HAB CRM:"
echo "   - Admin: https://api.digit-hab.altoppe.sn/admin/"
echo "   - API Docs: https://api.digit-hab.altoppe.sn/api/docs/"
echo "   - Health: https://api.digit-hab.altoppe.sn/health/"
echo ""
echo "📝 Prochaines Étapes:"
echo "   1. Créer un superuser pour DIGIT-HAB:"
echo "      cd $DIGITHAB_DIR"
echo "      docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
echo ""
echo "   2. Configurer le renouvellement automatique SSL:"
echo "      sudo crontab -e"
echo "      # Ajouter: 0 3 * * * certbot renew --quiet --post-hook 'cd /var/www/al-toppe && docker compose -f docker-compose.prod.yml restart nginx'"
echo ""
echo "   3. Configurer les backups automatiques"
echo ""
echo "✨ Tout est prêt ! Bon développement ! 🚀"
