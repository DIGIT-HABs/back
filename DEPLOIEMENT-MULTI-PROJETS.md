# 🚀 Déploiement Multi-Projets sur le Même VPS

**Situation** : Vous avez déjà `al-toppe` en production sur `/var/www/al-toppe`  
**Objectif** : Déployer DIGIT-HAB CRM à côté sans conflit

---

## 📋 Architecture Multi-Projets

```
VPS
├── /var/www/al-toppe/          (Projet existant)
│   ├── docker-compose.yml
│   ├── nginx (port 80, 443)
│   ├── PostgreSQL (port interne)
│   └── Redis (port interne)
│
└── /var/www/digit-hab-crm/     (Nouveau projet)
    ├── docker-compose.yml
    ├── nginx (ports différents ou domaine différent)
    ├── PostgreSQL (port interne)
    └── Redis (port interne)
```

---

## 🎯 Option 1 : Domaines Séparés (RECOMMANDÉ)

Chaque projet a son propre domaine/sous-domaine.

### Configuration

**Al-Toppe** : `al-toppe.com`, `api.al-toppe.com`  
**DIGIT-HAB** : `digit-hab.com`, `api.digit-hab.com`

### Avantages
- ✅ Isolation complète
- ✅ Pas de conflit de ports
- ✅ Nginx géré indépendamment
- ✅ Plus simple à maintenir

---

## 🔧 Déploiement Étape par Étape

### Étape 1 : Préparer le Dossier

```bash
# Se connecter au VPS
ssh digit-hab@VOTRE_IP

# Créer le dossier pour DIGIT-HAB CRM
sudo mkdir -p /var/www/digit-hab-crm
sudo chown digit-hab:digit-hab /var/www/digit-hab-crm
cd /var/www/digit-hab-crm
```

### Étape 2 : Transférer les Fichiers

**Depuis votre machine locale** :

```bash
# Aller dans votre projet local
cd c:/Users/soule/Documents/projet/2025/DIGIT-HAB_CRM_/CRM/Django

# Transférer via SCP
scp -r ./* digit-hab@VOTRE_IP:/var/www/digit-hab-crm/

# Ou via rsync (plus rapide pour les mises à jour)
rsync -avz --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
  ./* digit-hab@VOTRE_IP:/var/www/digit-hab-crm/
```

**Ou via Git** :

```bash
# Sur le VPS
cd /var/www/digit-hab-crm
git clone https://github.com/VOTRE_USERNAME/DIGIT-HAB_CRM.git .
```

### Étape 3 : Modifier le docker-compose.yml pour Éviter les Conflits

Créez un fichier `docker-compose.prod.yml` :

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: digit-hab-db  # ⚠️ Nom unique
    environment:
      POSTGRES_DB: ${DB_NAME:-digit_hab_crm_prod}
      POSTGRES_USER: ${DB_USER:-digit_hab_user}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - digit_hab_postgres_data:/var/lib/postgresql/data  # ⚠️ Volume unique
    networks:
      - digit-hab-network  # ⚠️ Network unique
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: digit-hab-redis  # ⚠️ Nom unique
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - digit_hab_redis_data:/data  # ⚠️ Volume unique
    networks:
      - digit-hab-network
    restart: unless-stopped

  web:
    build: .
    container_name: digit-hab-web  # ⚠️ Nom unique
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DB_NAME=${DB_NAME:-digit_hab_crm_prod}
      - DB_USER=${DB_USER:-digit_hab_user}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
    volumes:
      - ./staticfiles:/var/www/digit-hab/staticfiles
      - ./media:/var/www/digit-hab/media
    networks:
      - digit-hab-network
    restart: unless-stopped
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn --bind 0.0.0.0:8000 --workers 4 digit_hab_crm.wsgi:application"

  celery-worker:
    build: .
    container_name: digit-hab-celery-worker  # ⚠️ Nom unique
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DB_NAME=${DB_NAME:-digit_hab_crm_prod}
      - DB_USER=${DB_USER:-digit_hab_user}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/0
    volumes:
      - ./media:/app/media
    networks:
      - digit-hab-network
    restart: unless-stopped
    depends_on:
      - db
      - redis
    command: python -m celery -A digit_hab_crm worker --loglevel=info

  celery-beat:
    build: .
    container_name: digit-hab-celery-beat  # ⚠️ Nom unique
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DB_NAME=${DB_NAME:-digit_hab_crm_prod}
      - DB_USER=${DB_USER:-digit_hab_user}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432
      - CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/0
    networks:
      - digit-hab-network
    restart: unless-stopped
    depends_on:
      - db
      - redis
      - celery-worker
    command: python -m celery -A digit_hab_crm beat --loglevel=info

  nginx:
    image: nginx:alpine
    container_name: digit-hab-nginx  # ⚠️ Nom unique
    ports:
      - "8080:80"      # ⚠️ Port différent de al-toppe (80 → 8080)
      - "8443:443"     # ⚠️ Port différent de al-toppe (443 → 8443)
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./staticfiles:/var/www/digit-hab/staticfiles:ro
      - ./media:/var/www/digit-hab/media:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    networks:
      - digit-hab-network
    restart: unless-stopped

volumes:
  digit_hab_postgres_data:  # ⚠️ Nom unique
  digit_hab_redis_data:     # ⚠️ Nom unique

networks:
  digit-hab-network:        # ⚠️ Nom unique
    driver: bridge
```

### Étape 4 : Configurer l'Environnement

```bash
cd /var/www/digit-hab-crm

# Créer le fichier .env pour production
nano .env
```

Contenu du `.env` :

```bash
# Django Core
DEBUG=False
SECRET_KEY=VOTRE_SECRET_KEY_UNIQUE_DIFFERENTE_DE_AL_TOPPE
ALLOWED_HOSTS=digit-hab.com,api.digit-hab.com,www.digit-hab.com,VOTRE_IP

# Database
DB_NAME=digit_hab_crm_prod
DB_USER=digit_hab_user
DB_PASSWORD=VOTRE_MOT_DE_PASSE_POSTGRES_UNIQUE
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_PASSWORD=VOTRE_MOT_DE_PASSE_REDIS_UNIQUE
REDIS_URL=redis://:VOTRE_MOT_DE_PASSE_REDIS_UNIQUE@redis:6379/0

# Celery
CELERY_BROKER_URL=redis://:VOTRE_MOT_DE_PASSE_REDIS_UNIQUE@redis:6379/0
CELERY_RESULT_BACKEND=redis://:VOTRE_MOT_DE_PASSE_REDIS_UNIQUE@redis:6379/0

# Email (utilisez les mêmes si c'est le même compte)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre_email@gmail.com
EMAIL_HOST_PASSWORD=votre_app_password

# Cloudinary (créez un nouveau projet ou partagez)
CLOUDINARY_CLOUD_NAME=votre_cloud_name
CLOUDINARY_API_KEY=votre_api_key
CLOUDINARY_API_SECRET=votre_api_secret

# Stripe (créez un nouveau compte ou partagez)
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# CORS
CORS_ALLOWED_ORIGINS=https://digit-hab.com,https://app.digit-hab.com
```

### Étape 5 : Générer les Certificats SSL

**Option A : Let's Encrypt (si domaine configuré)**

```bash
# Arrêter temporairement al-toppe nginx pour libérer le port 80
cd /var/www/al-toppe
docker compose stop nginx

# Obtenir le certificat pour digit-hab
sudo certbot certonly --standalone \
  -d digit-hab.com \
  -d www.digit-hab.com \
  -d api.digit-hab.com \
  --email votre_email@gmail.com \
  --agree-tos

# Copier les certificats
sudo mkdir -p /var/www/digit-hab-crm/ssl
sudo cp /etc/letsencrypt/live/digit-hab.com/fullchain.pem /var/www/digit-hab-crm/ssl/
sudo cp /etc/letsencrypt/live/digit-hab.com/privkey.pem /var/www/digit-hab-crm/ssl/
sudo chown -R digit-hab:digit-hab /var/www/digit-hab-crm/ssl

# Redémarrer al-toppe nginx
cd /var/www/al-toppe
docker compose start nginx
```

**Option B : Certificat Auto-Signé (développement)**

```bash
cd /var/www/digit-hab-crm
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/privkey.pem \
  -out ssl/fullchain.pem \
  -subj "/C=SN/ST=Dakar/L=Dakar/O=DigitHab/CN=digit-hab.com"
```

### Étape 6 : Modifier nginx.conf

```bash
cd /var/www/digit-hab-crm
cp nginx.conf nginx.prod.conf
nano nginx.prod.conf
```

Assurez-vous que les chemins sont corrects :

```nginx
# Static files
location /static/ {
    alias /var/www/digit-hab/staticfiles/;  # ⚠️ Vérifier le chemin
    expires 30d;
}

location /media/ {
    alias /var/www/digit-hab/media/;  # ⚠️ Vérifier le chemin
    expires 30d;
}
```

### Étape 7 : Build et Démarrer

```bash
cd /var/www/digit-hab-crm

# Build les images
docker compose -f docker-compose.prod.yml build

# Démarrer les services
docker compose -f docker-compose.prod.yml up -d

# Voir les logs
docker compose -f docker-compose.prod.yml logs -f
```

### Étape 8 : Migrations et Setup

```bash
cd /var/www/digit-hab-crm

# Migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Créer un superuser
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Collecter les statiques
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Étape 9 : Vérifier que Tout Fonctionne

```bash
# Vérifier les conteneurs
docker ps

# Vous devriez voir :
# - al-toppe-db, al-toppe-redis, al-toppe-web, al-toppe-nginx
# - digit-hab-db, digit-hab-redis, digit-hab-web, digit-hab-nginx

# Tester l'accès
curl http://localhost:8080/health/
curl https://digit-hab.com/health/  # Si domaine configuré
```

---

## 🌐 Option 2 : Nginx Reverse Proxy Global (Avancé)

Si vous voulez que les deux projets utilisent les ports 80 et 443, configurez un nginx global.

### Architecture

```
Internet → Nginx Global (80, 443)
            ↓
            ├─→ al-toppe.com → al-toppe-web:8000
            └─→ digit-hab.com → digit-hab-web:8000
```

### Configuration

1. **Désactiver les nginx internes** dans les docker-compose
2. **Installer nginx globalement** sur le VPS
3. **Configurer les virtual hosts**

```bash
# Installer nginx sur le VPS
sudo apt install nginx

# Créer la config pour digit-hab
sudo nano /etc/nginx/sites-available/digit-hab.com
```

Contenu :

```nginx
upstream digit_hab_backend {
    server localhost:8001;  # Port du service web digit-hab
}

server {
    listen 80;
    server_name digit-hab.com www.digit-hab.com api.digit-hab.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name digit-hab.com www.digit-hab.com api.digit-hab.com;

    ssl_certificate /etc/letsencrypt/live/digit-hab.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/digit-hab.com/privkey.pem;

    location /static/ {
        alias /var/www/digit-hab-crm/staticfiles/;
    }

    location /media/ {
        alias /var/www/digit-hab-crm/media/;
    }

    location / {
        proxy_pass http://digit_hab_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Activer le site
sudo ln -s /etc/nginx/sites-available/digit-hab.com /etc/nginx/sites-enabled/

# Tester la config
sudo nginx -t

# Recharger nginx
sudo systemctl reload nginx
```

Modifiez ensuite le `docker-compose.prod.yml` pour exposer le web sur le port 8001 :

```yaml
web:
  ...
  ports:
    - "8001:8000"  # Exposer sur le port 8001
```

---

## 📊 Commandes Utiles Multi-Projets

### Gérer AL-TOPPE

```bash
cd /var/www/al-toppe
docker compose ps
docker compose logs -f
docker compose restart
```

### Gérer DIGIT-HAB

```bash
cd /var/www/digit-hab-crm
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml restart
```

### Voir Tous les Conteneurs

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Surveiller les Ressources

```bash
# Utiliser ctop
ctop

# Ou htop
htop

# Ou docker stats
docker stats
```

---

## 🔧 Maintenance

### Backup des Deux Projets

```bash
# Script de backup global
nano ~/backup-all-projects.sh
```

```bash
#!/bin/bash

BACKUP_DIR="/home/digit-hab/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup AL-TOPPE
cd /var/www/al-toppe
docker compose exec -T db pg_dump -U user dbname > $BACKUP_DIR/altoppe_db_$DATE.sql
tar -czf $BACKUP_DIR/altoppe_media_$DATE.tar.gz media/

# Backup DIGIT-HAB
cd /var/www/digit-hab-crm
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U digit_hab_user digit_hab_crm_prod > $BACKUP_DIR/digithab_db_$DATE.sql
tar -czf $BACKUP_DIR/digithab_media_$DATE.tar.gz media/

# Garder 7 jours
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
chmod +x ~/backup-all-projects.sh

# Ajouter au cron
crontab -e
# 0 2 * * * /home/digit-hab/backup-all-projects.sh
```

---

## ✅ Checklist de Déploiement

- [ ] Dossier `/var/www/digit-hab-crm` créé
- [ ] Fichiers transférés
- [ ] `.env` configuré avec des mots de passe uniques
- [ ] `docker-compose.prod.yml` avec noms de conteneurs uniques
- [ ] Certificats SSL générés
- [ ] Services démarrés
- [ ] Migrations appliquées
- [ ] Superuser créé
- [ ] Tests d'accès réussis
- [ ] Backup configuré

---

**🎉 Les deux projets cohabitent maintenant sur le même VPS !**

*Pour toute question : support@digit-hab.com*
