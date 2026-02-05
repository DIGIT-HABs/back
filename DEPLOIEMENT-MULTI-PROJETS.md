# 🌐 Déploiement Multi-Projets sur VPS

**Situation** : Vous avez déjà **al-toppe** en production et vous voulez ajouter **DIGIT-HAB CRM**

**Domaines** :
- Projet existant : `altoppe.sn` 
- Nouveau projet : `api.digit-hab.altoppe.sn`, `digit-hab.altoppe.sn`

---

## 📊 Architecture Actuelle

```
VPS (Ubuntu)
│
├── /var/www/al-toppe/               ← Projet existant
│   └── (Django sur port 8000)
│
├── Nginx Principal (Host)
│   ├── Port 80
│   └── Port 443 → altoppe.sn
│
└── Certificats SSL
    └── /etc/letsencrypt/live/altoppe.sn/
```

## 🎯 Architecture Cible

```
VPS (Ubuntu)
│
├── /var/www/al-toppe/               ← Projet 1
│   └── Docker Compose (port 8000)
│
├── /var/www/digit-hab-crm/          ← Projet 2 (NOUVEAU)
│   └── Docker Compose (port 8001)
│
├── Nginx Principal (Host)
│   ├── Port 80  → Redirection HTTPS
│   └── Port 443 →
│       ├── altoppe.sn → :8000 (al-toppe)
│       └── digit-hab.altoppe.sn → :8001 (digit-hab)
│
└── Certificats SSL
    ├── /etc/letsencrypt/live/altoppe.sn/
    └── /etc/letsencrypt/live/digit-hab.altoppe.sn/  ← NOUVEAU
```

---

## 🚀 Guide de Déploiement Étape par Étape

### ÉTAPE 1 : Obtenir les Certificats SSL

Puisque Nginx tourne déjà, utilisez le plugin nginx :

```bash
# Méthode 1 : Plugin Nginx (RECOMMANDÉ)
sudo certbot certonly --nginx \
  -d digit-hab.altoppe.sn \
  -d api.digit-hab.altoppe.sn \
  --email souleymane9700@gmail.com \
  --agree-tos

# OU Méthode 2 : Webroot
# sudo certbot certonly --webroot \
#   -w /var/www/certbot \
#   -d digit-hab.altoppe.sn \
#   -d api.digit-hab.altoppe.sn \
#   --email souleymane9700@gmail.com \
#   --agree-tos

# Vérifier les certificats
sudo ls -la /etc/letsencrypt/live/digit-hab.altoppe.sn/
```

### ÉTAPE 2 : Préparer les Dossiers

```bash
# Créer le dossier du projet
sudo mkdir -p /var/www/digit-hab-crm
sudo chown -R digit-hab:digit-hab /var/www/digit-hab-crm

# Créer les dossiers nécessaires
mkdir -p /var/www/digit-hab-crm/staticfiles
mkdir -p /var/www/digit-hab-crm/media
mkdir -p /var/www/digit-hab-crm/logs
```

### ÉTAPE 3 : Transférer le Projet

**Sur votre machine locale** :

```bash
# Aller dans le dossier Django
cd c:/Users/soule/Documents/projet/2025/DIGIT-HAB_CRM_/CRM/Django

# Transférer via SCP
scp -r . digit-hab@VOTRE_IP_VPS:/var/www/digit-hab-crm/

# OU via rsync (plus rapide pour les updates)
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' \
  . digit-hab@VOTRE_IP_VPS:/var/www/digit-hab-crm/
```

### ÉTAPE 4 : Configurer les Variables d'Environnement

**Sur le VPS** :

```bash
cd /var/www/digit-hab-crm

# Créer le fichier .env pour production
nano .env
```

**Contenu du `.env`** :

```bash
# ============================================
# DIGIT-HAB CRM - Production
# ============================================

# Django
DEBUG=False
SECRET_KEY=CHANGEZ_MOI_$(openssl rand -base64 50)
ALLOWED_HOSTS=digit-hab.altoppe.sn,api.digit-hab.altoppe.sn,VOTRE_IP_VPS

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=digit_hab_crm_prod
DB_USER=digit_hab_user
DB_PASSWORD=CHANGEZ_MOI_PASSWORD_POSTGRES_123
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_PASSWORD=CHANGEZ_MOI_PASSWORD_REDIS_456
REDIS_URL=redis://:CHANGEZ_MOI_PASSWORD_REDIS_456@redis:6379/0

# Celery
CELERY_BROKER_URL=redis://:CHANGEZ_MOI_PASSWORD_REDIS_456@redis:6379/0
CELERY_RESULT_BACKEND=redis://:CHANGEZ_MOI_PASSWORD_REDIS_456@redis:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=souleymane9700@gmail.com
EMAIL_HOST_PASSWORD=aknr icmy elir eccj

# Cloudinary
CLOUDINARY_CLOUD_NAME=dxjmr9een
CLOUDINARY_API_KEY=787852268875218
CLOUDINARY_API_SECRET=6LstMR8csQDQVeFcFdYZXxRlwow

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_51Opr31I9ZCLc3CRBzCBXOXZpCQVprlz5pdTBNFQ3npDtljGhVLYIrS1XP7UU0dEBxvZLQi4JXHGG8imuStxmwYfB00nsAPigUa
STRIPE_SECRET_KEY=sk_test_51Opr31I9ZCLc3CRBj6e5MW4LzxLJat0MgmGPg9gvfZldVZ8TIiW0bwrIzJkcX9f2xrLs7W0Q3ELxqx8jOEZvnRoc00sv8jlMhL
STRIPE_WEBHOOK_SECRET=whsec_2d33dd5cc8e0dcc55f1fd43c908e31fb5de3e2c97b1beb9c24954b42063d9c5d
STRIPE_CURRENCY=xof

# CORS
CORS_ALLOWED_ORIGINS=https://digit-hab.altoppe.sn,https://api.digit-hab.altoppe.sn

# Security
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### ÉTAPE 5 : Configurer Nginx Principal

**Sur le VPS** :

```bash
# Créer le fichier de configuration
sudo nano /etc/nginx/sites-available/digit-hab
```

Copiez le contenu de `nginx-site.conf` (que j'ai créé ci-dessus).

```bash
# Créer un lien symbolique
sudo ln -s /etc/nginx/sites-available/digit-hab /etc/nginx/sites-enabled/

# Tester la configuration
sudo nginx -t

# Si OK, recharger Nginx
sudo systemctl reload nginx
```

### ÉTAPE 6 : Ajouter Rate Limiting dans Nginx Principal

```bash
# Éditer la configuration principale
sudo nano /etc/nginx/nginx.conf
```

Ajouter dans le bloc `http` (s'il n'existe pas déjà) :

```nginx
http {
    # ... autres configurations ...
    
    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    
    # ... reste de la configuration ...
}
```

### ÉTAPE 7 : Déployer l'Application

```bash
cd /var/www/digit-hab-crm

# Build les images Docker
docker compose -f docker-compose.prod.yml build

# Démarrer tous les services
docker compose -f docker-compose.prod.yml up -d

# Voir les logs
docker compose -f docker-compose.prod.yml logs -f
```

### ÉTAPE 8 : Setup Initial de la Base de Données

```bash
# Migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Créer un superuser
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Collecter les statiques
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Créer l'agence et des données de test
docker compose -f docker-compose.prod.yml exec web python create_clients.py
```

### ÉTAPE 9 : Vérifier le Déploiement

```bash
# Vérifier les conteneurs
docker compose -f docker-compose.prod.yml ps

# Tester les endpoints
curl http://localhost:8001/health/
curl https://digit-hab.altoppe.sn/health/
curl https://api.digit-hab.altoppe.sn/api/

# Tester l'admin
# Ouvrir dans le navigateur : https://digit-hab.altoppe.sn/admin/
```

---

## 🔒 Configuration SSL - Détails

### Obtenir les Certificats avec Nginx en Marche

```bash
# Option A : Plugin Nginx (plus simple)
sudo certbot certonly --nginx \
  -d digit-hab.altoppe.sn \
  -d api.digit-hab.altoppe.sn

# Option B : Webroot
# 1. Créer le dossier webroot
sudo mkdir -p /var/www/certbot

# 2. Ajouter dans votre config Nginx temporairement
sudo nano /etc/nginx/sites-available/digit-hab-temp

# Contenu :
# server {
#     listen 80;
#     server_name digit-hab.altoppe.sn api.digit-hab.altoppe.sn;
#     location /.well-known/acme-challenge/ {
#         root /var/www/certbot;
#     }
# }

# 3. Activer et recharger
sudo ln -s /etc/nginx/sites-available/digit-hab-temp /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 4. Obtenir les certificats
sudo certbot certonly --webroot \
  -w /var/www/certbot \
  -d digit-hab.altoppe.sn \
  -d api.digit-hab.altoppe.sn

# 5. Supprimer la config temporaire
sudo rm /etc/nginx/sites-enabled/digit-hab-temp
```

---

## 📋 Checklist de Déploiement

### Avant le Déploiement

- [ ] DNS configuré (digit-hab.altoppe.sn → IP VPS)
- [ ] Docker installé et fonctionnel
- [ ] Code transféré sur le VPS (`/var/www/digit-hab-crm/`)
- [ ] Fichier `.env` configuré avec les bonnes valeurs
- [ ] `docker-compose.prod.yml` utilise le port 8001 (pas de conflit)

### Certificats SSL

- [ ] Certificats Let's Encrypt obtenus
- [ ] Certificats valides pour `digit-hab.altoppe.sn`
- [ ] Certificats valides pour `api.digit-hab.altoppe.sn`
- [ ] Renouvellement automatique configuré

### Configuration Nginx

- [ ] Fichier `/etc/nginx/sites-available/digit-hab` créé
- [ ] Lien symbolique dans `/etc/nginx/sites-enabled/`
- [ ] Configuration testée (`sudo nginx -t`)
- [ ] Nginx rechargé (`sudo systemctl reload nginx`)
- [ ] Rate limiting configuré

### Application Docker

- [ ] Images buildées (`docker compose build`)
- [ ] Services démarrés (`docker compose up -d`)
- [ ] Tous les conteneurs running (`docker compose ps`)
- [ ] Migrations appliquées
- [ ] Statiques collectés
- [ ] Superuser créé

### Tests

- [ ] Health check : https://digit-hab.altoppe.sn/health/
- [ ] Admin accessible : https://digit-hab.altoppe.sn/admin/
- [ ] API fonctionne : https://api.digit-hab.altoppe.sn/api/
- [ ] CORS configuré correctement
- [ ] HTTPS fonctionne (redirect HTTP → HTTPS)

---

## 🔧 Commandes sur le VPS

### Résumé Complet (Copier-Coller)

```bash
# ============================================
# DÉPLOIEMENT DIGIT-HAB CRM - VPS
# ============================================

# 1. Obtenir les certificats SSL
sudo certbot certonly --nginx \
  -d digit-hab.altoppe.sn \
  -d api.digit-hab.altoppe.sn \
  --email souleymane9700@gmail.com \
  --agree-tos

# 2. Vérifier les certificats
sudo ls -la /etc/letsencrypt/live/digit-hab.altoppe.sn/

# 3. Aller dans le dossier du projet
cd /var/www/digit-hab-crm

# 4. Vérifier le fichier .env
cat .env | head -20

# 5. Build et démarrer
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 6. Migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# 7. Créer superuser
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# 8. Collecter statiques
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 9. Configurer Nginx
sudo nano /etc/nginx/sites-available/digit-hab
# Copier le contenu de nginx-site.conf

# 10. Activer le site
sudo ln -s /etc/nginx/sites-available/digit-hab /etc/nginx/sites-enabled/

# 11. Tester et recharger Nginx
sudo nginx -t
sudo systemctl reload nginx

# 12. Vérifier les services
docker compose -f docker-compose.prod.yml ps

# 13. Tester l'application
curl https://digit-hab.altoppe.sn/health/
curl https://api.digit-hab.altoppe.sn/api/
```

---

## 🎯 Résolution du Problème Port 80

Puisque le port 80 est déjà utilisé par votre Nginx principal (pour al-toppe), vous avez **déjà la bonne approche** :

### ✅ Ce Qu'il Faut Faire

1. **Docker Compose** : N'expose PAS les ports 80/443
   - Utilise `docker-compose.prod.yml` avec port `8001:8000`
   - Nginx interne Docker **désactivé** ou retiré

2. **Nginx Principal** : Gère tous les domaines
   - `altoppe.sn` → localhost:8000 (projet al-toppe)
   - `digit-hab.altoppe.sn` → localhost:8001 (digit-hab-crm)

3. **Certificats SSL** : Obtenus via plugin nginx
   - Ne bloque pas le port 80
   - Utilise le Nginx déjà en marche

---

## 📝 Configuration .env pour Production

```bash
cd /var/www/digit-hab-crm
nano .env
```

**Valeurs IMPORTANTES à changer** :

```bash
DEBUG=False                          # ⚠️ CRITICAL
SECRET_KEY=...                       # ⚠️ GÉNÉRER UNE NOUVELLE
ALLOWED_HOSTS=digit-hab.altoppe.sn,api.digit-hab.altoppe.sn

# Générer une nouvelle SECRET_KEY
docker run --rm python:3.11 python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🔄 Gestion des Deux Projets

### Voir les Services en Cours

```bash
# Projet al-toppe
cd /var/www/al-toppe
docker compose ps

# Projet digit-hab-crm
cd /var/www/digit-hab-crm
docker compose -f docker-compose.prod.yml ps

# Tous les conteneurs Docker
docker ps
```

### Logs

```bash
# al-toppe
docker compose -f /var/www/al-toppe/docker-compose.yml logs -f

# digit-hab-crm
docker compose -f /var/www/digit-hab-crm/docker-compose.prod.yml logs -f web

# Nginx principal
sudo tail -f /var/log/nginx/digit-hab-access.log
sudo tail -f /var/log/nginx/digit-hab-error.log
```

### Redémarrer un Projet

```bash
# Redémarrer digit-hab-crm
cd /var/www/digit-hab-crm
docker compose -f docker-compose.prod.yml restart

# Redémarrer al-toppe
cd /var/www/al-toppe
docker compose restart
```

---

## 🐛 Problèmes Courants

### Problème : Port 8001 déjà utilisé

```bash
# Vérifier qui utilise le port
sudo lsof -i :8001
sudo netstat -tulpn | grep 8001

# Changer le port dans docker-compose.prod.yml
# ports:
#   - "8002:8000"  # Utiliser 8002 au lieu de 8001

# Puis mettre à jour nginx-site.conf
# upstream digit_hab_backend {
#     server localhost:8002;
# }
```

### Problème : Nginx ne démarre pas

```bash
# Tester la configuration
sudo nginx -t

# Voir les erreurs
sudo journalctl -u nginx -n 50

# Vérifier les logs
sudo tail -f /var/log/nginx/error.log
```

### Problème : Application Django ne répond pas

```bash
# Vérifier les logs Docker
docker compose -f docker-compose.prod.yml logs web

# Vérifier que le conteneur est UP
docker compose -f docker-compose.prod.yml ps

# Tester en local sur le VPS
curl http://localhost:8001/health/
```

---

## 📊 Monitoring des Deux Projets

### Créer un Script de Status

```bash
nano ~/check-status.sh
```

```bash
#!/bin/bash

echo "╔════════════════════════════════════════════╗"
echo "║     STATUS DES PROJETS - VPS               ║"
echo "╚════════════════════════════════════════════╝"
echo ""

echo "📊 AL-TOPPE:"
cd /var/www/al-toppe
docker compose ps
echo ""

echo "📊 DIGIT-HAB CRM:"
cd /var/www/digit-hab-crm
docker compose -f docker-compose.prod.yml ps
echo ""

echo "🌐 NGINX:"
sudo systemctl status nginx --no-pager | head -5
echo ""

echo "💾 ESPACE DISQUE:"
df -h | grep -E 'Filesystem|/dev/vda|/dev/sda'
echo ""

echo "🔥 MÉMOIRE:"
free -h
echo ""

echo "✅ Vérification terminée!"
```

```bash
chmod +x ~/check-status.sh
./check-status.sh
```

---

## 🎉 Résumé Final

### Ce Qu'il Faut Faire sur le VPS

1. **Obtenir SSL** (avec Nginx qui tourne) :
   ```bash
   sudo certbot certonly --nginx \
     -d digit-hab.altoppe.sn \
     -d api.digit-hab.altoppe.sn
   ```

2. **Configurer Nginx** :
   ```bash
   sudo nano /etc/nginx/sites-available/digit-hab
   # Copier nginx-site.conf
   sudo ln -s /etc/nginx/sites-available/digit-hab /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```

3. **Déployer Docker** :
   ```bash
   cd /var/www/digit-hab-crm
   docker compose -f docker-compose.prod.yml up -d
   docker compose -f docker-compose.prod.yml exec web python manage.py migrate
   docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
   docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
   ```

4. **Tester** :
   ```bash
   curl https://api.digit-hab.altoppe.sn/api/
   ```

---

**🚀 Continuez et dites-moi où vous en êtes !**