#!/bin/bash

echo "════════════════════════════════════════════════════════"
echo "  Déploiement DIGIT-HAB CRM avec AL-TOPPE existant"
echo "════════════════════════════════════════════════════════"
echo ""

# Variables
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

# Étape 1 : Arrêter Nginx Docker d'al-toppe
echo "🛑 Arrêt temporaire de Nginx (al-toppe)..."
cd $ALTOPPE_DIR
docker compose stop nginx
sleep 2

# Vérifier que les ports sont libres
if sudo lsof -i :80 > /dev/null 2>&1; then
    echo "❌ Port 80 encore utilisé !"
    sudo lsof -i :80
    exit 1
fi

# Étape 2 : Obtenir les certificats
echo "🔒 Obtention des certificats SSL..."
sudo certbot certonly --standalone \
  -d $DOMAIN1 \
  -d $DOMAIN2 \
  --email $EMAIL \
  --agree-tos \
  --non-interactive

# Vérifier que les certificats ont été créés
if [ ! -d "/etc/letsencrypt/live/$DOMAIN1" ]; then
    echo "❌ Échec de création des certificats !"
    cd $ALTOPPE_DIR
    docker compose start nginx
    exit 1
fi

echo "✅ Certificats obtenus !"
sudo ls -la /etc/letsencrypt/live/$DOMAIN1/

# Étape 3 : Redémarrer Nginx d'al-toppe
echo "🔄 Redémarrage de Nginx (al-toppe)..."
cd $ALTOPPE_DIR
docker compose start nginx
sleep 2

# Étape 4 : Déployer DIGIT-HAB CRM
echo "🚀 Déploiement de DIGIT-HAB CRM..."
cd $DIGITHAB_DIR

# Build les images
echo "🔨 Build des images Docker..."
docker compose -f docker-compose.prod.yml build

# Démarrer les services
echo "▶️  Démarrage des services..."
docker compose -f docker-compose.prod.yml up -d

# Attendre que la DB soit prête
echo "⏳ Attente de la base de données..."
sleep 10

# Migrations
echo "🗄️  Application des migrations..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Collecte des statiques
echo "📦 Collecte des fichiers statiques..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Étape 5 : Configurer Nginx pour DIGIT-HAB
echo "🌐 Configuration de Nginx..."

# Créer la configuration Nginx pour DIGIT-HAB
sudo tee /etc/nginx/sites-available/digit-hab > /dev/null <<'EOF'
upstream digit_hab_backend {
    server localhost:8001;
}

server {
    listen 80;
    server_name digit-hab.altoppe.sn api.digit-hab.altoppe.sn;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name digit-hab.altoppe.sn api.digit-hab.altoppe.sn;

    ssl_certificate /etc/letsencrypt/live/digit-hab.altoppe.sn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/digit-hab.altoppe.sn/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 20M;

    access_log /var/log/nginx/digit-hab-access.log;
    error_log /var/log/nginx/digit-hab-error.log;

    location /static/ {
        alias /var/www/digit-hab-crm/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /var/www/digit-hab-crm/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://digit_hab_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Activer le site
sudo ln -sf /etc/nginx/sites-available/digit-hab /etc/nginx/sites-enabled/

# Tester la configuration
sudo nginx -t

# Si le service nginx est masqué, démasquer et activer
sudo systemctl unmask nginx
sudo systemctl enable nginx
sudo systemctl start nginx

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Déploiement terminé !"
echo "════════════════════════════════════════════════════════"
echo ""
echo "🎯 Services démarrés:"
docker compose -f $DIGITHAB_DIR/docker-compose.prod.yml ps
echo ""
echo "🌐 URLs à tester:"
echo "   - https://digit-hab.altoppe.sn/admin/"
echo "   - https://api.digit-hab.altoppe.sn/api/"
echo "   - https://api.digit-hab.altoppe.sn/health/"
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Créer un superuser:"
echo "      docker compose -f $DIGITHAB_DIR/docker-compose.prod.yml exec web python manage.py createsuperuser"
echo ""
echo "   2. Tester l'API:"
echo "      curl https://api.digit-hab.altoppe.sn/health/"
echo ""
echo "✨ C'est prêt !"
