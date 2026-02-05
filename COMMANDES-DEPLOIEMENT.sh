#!/bin/bash
# ════════════════════════════════════════════════════════
# Commandes de Déploiement Rapide - DIGIT-HAB CRM
# À exécuter sur le VPS en tant que root
# ════════════════════════════════════════════════════════

# ✅ 1. Vérifier DNS
echo "=== 1. Vérification DNS ==="
dig digit-hab.altoppe.sn +short
dig api.digit-hab.altoppe.sn +short

# ✅ 2. Créer les dossiers
echo "=== 2. Création des dossiers ==="
mkdir -p /var/www/certbot
mkdir -p /var/www/digit-hab-crm/staticfiles
mkdir -p /var/www/digit-hab-crm/media
chown -R digit-hab:digit-hab /var/www/certbot
chown -R digit-hab:digit-hab /var/www/digit-hab-crm

# ✅ 3. Backup AL-TOPPE
echo "=== 3. Backup de la config AL-TOPPE ==="
cd /var/www/al-toppe
cp nginx.prod.conf nginx.prod.conf.backup.$(date +%Y%m%d_%H%M%S)
cp docker-compose.prod.yml docker-compose.prod.yml.backup.$(date +%Y%m%d_%H%M%S)

# ✅ 4. Obtenir les certificats SSL
echo "=== 4. Obtention des certificats SSL ==="
# D'abord, modifier nginx.prod.conf pour ajouter le webroot
# Voir GUIDE-DEPLOIEMENT-MANUEL.md section 4.1

# Redémarrer Nginx d'AL-TOPPE
cd /var/www/al-toppe
docker compose -f docker-compose.prod.yml restart nginx

# Obtenir les certificats
certbot certonly --webroot \
  -w /var/www/certbot \
  -d digit-hab.altoppe.sn \
  -d api.digit-hab.altoppe.sn \
  --email souleymane9700@gmail.com \
  --agree-tos \
  --non-interactive

# Vérifier
ls -la /etc/letsencrypt/live/digit-hab.altoppe.sn/

# ✅ 5. Déployer DIGIT-HAB
echo "=== 5. Déploiement DIGIT-HAB ==="
cd /var/www/digit-hab-crm

# Build
docker compose -f docker-compose.prod.yml build --no-cache

# Démarrer
docker compose -f docker-compose.prod.yml up -d

# Attendre la DB
sleep 15

# Migrations
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Collecte statiques
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Vérifier
docker compose -f docker-compose.prod.yml ps

# ✅ 6. Tests
echo "=== 6. Tests ==="
curl -I http://localhost:8001/health/
curl -I https://api.digit-hab.altoppe.sn/health/

# ✅ 7. Logs
echo "=== 7. Vérifier les logs ==="
docker compose -f docker-compose.prod.yml logs -f --tail=50
