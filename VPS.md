# 🚀 Guide de Déploiement VPS - DIGIT-HAB CRM

**Version**: 1.0  
**Date**: Février 2026  
**Environnement**: Production avec Docker Compose

---

## 📋 Table des Matières

1. [Prérequis](#prérequis)
2. [Préparation du VPS](#préparation-du-vps)
3. [Installation Docker](#installation-docker)
4. [Configuration de l'Application](#configuration-de-lapplication)
5. [Configuration SSL/HTTPS](#configuration-sslhttps)
6. [Déploiement](#déploiement)
7. [Post-Déploiement](#post-déploiement)
8. [Maintenance](#maintenance)
9. [Dépannage](#dépannage)

---

## 🎯 Prérequis

### VPS Recommandé
- **CPU**: 2 vCPUs minimum
- **RAM**: 4GB minimum (8GB recommandé)
- **Stockage**: 50GB SSD minimum
- **OS**: Ubuntu 22.04 LTS
- **IP**: Adresse IP publique fixe

### Domaine
- Domaine configuré pointant vers l'IP du VPS
- Exemple: `digit-hab.com`, `api.digit-hab.altoppe.sn`

### Accès
- Accès SSH root ou sudo

---

## 🔧 Préparation du VPS

### Étape 1 : Connexion SSH

```bash
# Se connecter au VPS
ssh root@VOTRE_IP_VPS

# Ou avec un utilisateur sudo
ssh votre_utilisateur@VOTRE_IP_VPS
```

### Étape 2 : Mise à Jour du Système

```bash
# Mettre à jour les paquets
sudo apt update && sudo apt upgrade -y

# Installer les outils essentiels
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    ufw \
    ca-certificates \
    gnupg \
    lsb-release
```

### Étape 3 : Configuration du Firewall

```bash
# Activer le firewall
sudo ufw enable

# Autoriser SSH (IMPORTANT avant d'activer UFW!)
sudo ufw allow 22/tcp

# Autoriser HTTP et HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Vérifier le statut
sudo ufw status
```

### Étape 4 : Créer un Utilisateur pour l'Application

```bash
# Créer l'utilisateur digit-hab
sudo adduser digit-hab

# Ajouter aux groupes nécessaires
sudo usermod -aG sudo digit-hab
sudo usermod -aG docker digit-hab  # On ajoutera docker plus tard

# Se connecter avec le nouvel utilisateur
su - digit-hab
```

---

## 🐳 Installation Docker

### Étape 1 : Installation de Docker

```bash
# Supprimer les anciennes versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Ajouter la clé GPG officielle de Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Ajouter le dépôt Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Mettre à jour et installer Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Vérifier l'installation
docker --version
docker compose version
```

### Étape 2 : Configurer Docker pour l'Utilisateur

```bash
# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER

# Appliquer les changements (ou se reconnecter)
newgrp docker

# Tester Docker sans sudo
docker run hello-world
```

### Étape 3 : Configurer Docker pour la Production

```bash
# Créer le fichier de configuration Docker
sudo mkdir -p /etc/docker

sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF

# Redémarrer Docker
sudo systemctl restart docker
sudo systemctl enable docker
```

---

## ⚙️ Configuration de l'Application

### Étape 1 : Cloner le Projet

```bash
# Aller dans le home directory
cd ~

# Cloner le repository (ou transférer les fichiers)
# Option 1 : Via Git
git clone https://github.com/VOTRE_USERNAME/DIGIT-HAB_CRM.git
cd DIGIT-HAB_CRM/Django

# Option 2 : Via SCP depuis votre machine locale
# Sur votre machine locale :
# scp -r ./Django digit-hab@VOTRE_IP:/home/digit-hab/digit-hab-crm/
```

### Étape 2 : Configurer les Variables d'Environnement

```bash
# Créer le fichier .env.prod
cd ~/DIGIT-HAB_CRM/Django  # ou le chemin où vous avez mis le projet
cp .env .env.prod

# Éditer le fichier .env.prod
nano .env.prod
```

**Contenu du fichier `.env.prod`** :

```bash
# ============================================
# DIGIT-HAB CRM - Configuration Production
# ============================================

# Django Core
DEBUG=False
SECRET_KEY=CHANGEZ_MOI_AVEC_UNE_CLE_SECRETE_LONGUE_ET_ALEATOIRE_123456789
ALLOWED_HOSTS=digit-hab.com,api.digit-hab.com,www.digit-hab.com,VOTRE_IP_VPS

# Database PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=digit_hab_crm_prod
DB_USER=digit_hab_user
DB_PASSWORD=CHANGEZ_MOI_MOT_DE_PASSE_POSTGRES_SECURISE
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://:CHANGEZ_MOI_MOT_DE_PASSE_REDIS@redis:6379/0
REDIS_PASSWORD=CHANGEZ_MOI_MOT_DE_PASSE_REDIS

# Celery
CELERY_BROKER_URL=redis://:CHANGEZ_MOI_MOT_DE_PASSE_REDIS@redis:6379/0
CELERY_RESULT_BACKEND=redis://:CHANGEZ_MOI_MOT_DE_PASSE_REDIS@redis:6379/0

# JWT Configuration
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# Email Configuration (Gmail)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre_email@gmail.com
EMAIL_HOST_PASSWORD=votre_app_password_gmail

# Cloudinary (Stockage fichiers)
CLOUDINARY_CLOUD_NAME=votre_cloud_name
CLOUDINARY_API_KEY=votre_api_key
CLOUDINARY_API_SECRET=votre_api_secret

# Stripe (Paiements)
STRIPE_PUBLISHABLE_KEY=pk_live_VOTRE_CLE
STRIPE_SECRET_KEY=sk_live_VOTRE_CLE
STRIPE_WEBHOOK_SECRET=whsec_VOTRE_SECRET
STRIPE_CURRENCY=xof

# CORS Origins (votre frontend)
CORS_ALLOWED_ORIGINS=https://digit-hab.com,https://www.digit-hab.com,https://app.digit-hab.com

# Security
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

**🔐 IMPORTANT : Générer une Secret Key sécurisée** :

```bash
# Générer une nouvelle SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Étape 3 : Créer le Fichier nginx.prod.conf

```bash
# Le docker-compose.yml référence nginx.prod.conf
# Copier votre nginx.conf existant
cp nginx.conf nginx.prod.conf

# Éditer pour production
nano nginx.prod.conf
```

Vérifiez que les domaines sont corrects dans `nginx.prod.conf` :

```nginx
server_name digit-hab.com www.digit-hab.com api.digit-hab.com;
```

---

## 🔒 Configuration SSL/HTTPS

### Option 1 : Let's Encrypt avec Certbot (RECOMMANDÉ)

```bash
# Installer Certbot
sudo apt install -y certbot

# Créer le dossier SSL
mkdir -p ~/DIGIT-HAB_CRM/Django/ssl

# Option A : Obtenir le certificat (serveur doit être arrêté)
sudo certbot certonly --standalone \
  -d digit-hab.com \
  -d www.digit-hab.com \
  -d api.digit-hab.com \
  --email votre_email@gmail.com \
  --agree-tos

# Copier les certificats
sudo cp /etc/letsencrypt/live/digit-hab.com/fullchain.pem ~/DIGIT-HAB_CRM/Django/ssl/
sudo cp /etc/letsencrypt/live/digit-hab.com/privkey.pem ~/DIGIT-HAB_CRM/Django/ssl/
sudo chown digit-hab:digit-hab ~/DIGIT-HAB_CRM/Django/ssl/*.pem
```

### Option 2 : Certificat Auto-Signé (DÉVELOPPEMENT UNIQUEMENT)

```bash
# Générer un certificat auto-signé
mkdir -p ~/DIGIT-HAB_CRM/Django/ssl
cd ~/DIGIT-HAB_CRM/Django/ssl

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem \
  -out fullchain.pem \
  -subj "/C=SN/ST=Dakar/L=Dakar/O=DigitHab/CN=digit-hab.com"
```

### Renouvellement Automatique Let's Encrypt

```bash
# Tester le renouvellement
sudo certbot renew --dry-run

# Créer un cron job pour le renouvellement
sudo crontab -e

# Ajouter cette ligne :
0 3 * * * certbot renew --quiet && cp /etc/letsencrypt/live/digit-hab.com/*.pem /home/digit-hab/DIGIT-HAB_CRM/Django/ssl/ && docker compose -f /home/digit-hab/DIGIT-HAB_CRM/Django/docker-compose.yml restart nginx
```

---

## 🚀 Déploiement

### Étape 1 : Vérifier les Fichiers

```bash
cd ~/DIGIT-HAB_CRM/Django

# Vérifier que tous les fichiers nécessaires sont présents
ls -la
# Doit contenir :
# - Dockerfile
# - docker-compose.yml
# - nginx.prod.conf
# - .env.prod (ou renommer .env)
# - requirements.txt
# - manage.py
# - ssl/ (avec les certificats)
```

### Étape 2 : Utiliser le Bon Fichier .env

```bash
# Renommer .env.prod en .env
mv .env .env.dev.backup  # Sauvegarder l'ancien
mv .env.prod .env

# Ou créer un lien symbolique
# ln -s .env.prod .env
```

### Étape 3 : Build et Démarrage

```bash
# Build les images Docker
docker compose build

# Démarrer tous les services
docker compose up -d

# Voir les logs
docker compose logs -f
```

### Étape 4 : Migrations et Setup Initial

```bash
# Créer la base de données et les tables
docker compose exec web python manage.py migrate

# Créer un superuser
docker compose exec web python manage.py createsuperuser

# Collecter les fichiers statiques
docker compose exec web python manage.py collectstatic --noinput

# Créer des données de test (optionnel)
docker compose exec web python create_clients.py
```

### Étape 5 : Vérifier les Services

```bash
# Vérifier que tous les conteneurs sont up
docker compose ps

# Devrait afficher :
# - db (postgres)
# - redis
# - web (django)
# - celery-worker
# - celery-beat
# - nginx

# Tester les endpoints
curl http://localhost/health/
curl https://digit-hab.com/health/
curl https://digit-hab.com/api/
```

---

## ✅ Post-Déploiement

### Étape 1 : Configurer les Logs

```bash
# Créer le dossier logs
mkdir -p ~/DIGIT-HAB_CRM/Django/logs

# Voir les logs en temps réel
docker compose logs -f web
docker compose logs -f nginx
docker compose logs -f celery-worker
```

### Étape 2 : Backup Automatique

Créer un script de backup :

```bash
# Créer le script backup
nano ~/backup-digit-hab.sh
```

Contenu :

```bash
#!/bin/bash

BACKUP_DIR="/home/digit-hab/backups"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/home/digit-hab/DIGIT-HAB_CRM/Django"

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker compose -f $PROJECT_DIR/docker-compose.yml exec -T db \
  pg_dump -U digit_hab_user digit_hab_crm_prod > $BACKUP_DIR/db_$DATE.sql

# Backup Media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C $PROJECT_DIR media/

# Garder seulement les 7 derniers backups
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Rendre exécutable
chmod +x ~/backup-digit-hab.sh

# Ajouter au cron (backup quotidien à 2h du matin)
crontab -e
# Ajouter :
0 2 * * * /home/digit-hab/backup-digit-hab.sh >> /home/digit-hab/backup.log 2>&1
```

### Étape 3 : Monitoring

```bash
# Installer ctop pour monitoring
sudo wget https://github.com/bcicen/ctop/releases/download/v0.7.7/ctop-0.7.7-linux-amd64 \
  -O /usr/local/bin/ctop
sudo chmod +x /usr/local/bin/ctop

# Utiliser
ctop
```

### Étape 4 : Tester l'Application

1. **Admin Django** : https://digit-hab.com/admin/
2. **API** : https://digit-hab.com/api/
3. **Documentation API** : https://digit-hab.com/api/docs/
4. **Health Check** : https://digit-hab.com/health/

### Étape 5 : Configurer le DNS

Dans votre registrar de domaine (ex: OVH, Namecheap, etc.) :

```
Type    Host    Value               TTL
A       @       VOTRE_IP_VPS        3600
A       www     VOTRE_IP_VPS        3600
A       api     VOTRE_IP_VPS        3600
CNAME   www     digit-hab.com       3600
```

---

## 🔧 Maintenance

### Mettre à Jour l'Application

```bash
cd ~/DIGIT-HAB_CRM/Django

# Pull les dernières modifications
git pull origin main

# Rebuild et redémarrer
docker compose down
docker compose build
docker compose up -d

# Migrations si nécessaire
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
```

### Voir les Logs

```bash
# Logs de tous les services
docker compose logs -f

# Logs d'un service spécifique
docker compose logs -f web
docker compose logs -f nginx
docker compose logs -f celery-worker

# Dernières 100 lignes
docker compose logs --tail=100 web
```

### Redémarrer les Services

```bash
# Redémarrer tous les services
docker compose restart

# Redémarrer un service spécifique
docker compose restart web
docker compose restart nginx

# Arrêter et redémarrer complètement
docker compose down
docker compose up -d
```

### Nettoyer Docker

```bash
# Supprimer les images inutilisées
docker system prune -a

# Supprimer les volumes orphelins
docker volume prune

# Voir l'espace disque utilisé
docker system df
```

---

## 🐛 Dépannage

### Problème 1 : Erreur 502 Bad Gateway

```bash
# Vérifier que le service web est up
docker compose ps

# Voir les logs
docker compose logs web

# Solution : Redémarrer le service
docker compose restart web
```

### Problème 2 : Base de Données ne Démarre Pas

```bash
# Voir les logs PostgreSQL
docker compose logs db

# Vérifier les permissions
docker compose down
sudo rm -rf postgres_data  # ATTENTION : Supprime les données !
docker compose up -d
docker compose exec web python manage.py migrate
```

### Problème 3 : Certificat SSL Expiré

```bash
# Renouveler le certificat
sudo certbot renew

# Copier les nouveaux certificats
sudo cp /etc/letsencrypt/live/digit-hab.com/*.pem ~/DIGIT-HAB_CRM/Django/ssl/

# Redémarrer nginx
docker compose restart nginx
```

### Problème 4 : Celery ne Traite pas les Tâches

```bash
# Voir les logs Celery
docker compose logs celery-worker
docker compose logs celery-beat

# Vérifier Redis
docker compose exec redis redis-cli ping
# Devrait retourner: PONG

# Redémarrer Celery
docker compose restart celery-worker celery-beat
```

### Problème 5 : Manque d'Espace Disque

```bash
# Voir l'utilisation du disque
df -h

# Nettoyer Docker
docker system prune -a --volumes

# Nettoyer les logs
sudo journalctl --vacuum-size=100M

# Supprimer les anciens backups
find ~/backups -type f -mtime +30 -delete
```

---

## 📊 Commandes Utiles

### Docker Compose

```bash
# Démarrer
docker compose up -d

# Arrêter
docker compose down

# Voir les services
docker compose ps

# Logs
docker compose logs -f [service]

# Exécuter une commande
docker compose exec web python manage.py shell

# Rebuild
docker compose build [service]

# Redémarrer
docker compose restart [service]
```

### Django Management

```bash
# Shell Django
docker compose exec web python manage.py shell

# Migrations
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Créer superuser
docker compose exec web python manage.py createsuperuser

# Collecter statiques
docker compose exec web python manage.py collectstatic

# Nettoyer sessions expirées
docker compose exec web python manage.py clearsessions
```

### Base de Données

```bash
# Backup
docker compose exec db pg_dump -U digit_hab_user digit_hab_crm_prod > backup.sql

# Restore
cat backup.sql | docker compose exec -T db psql -U digit_hab_user digit_hab_crm_prod

# Accéder à PostgreSQL
docker compose exec db psql -U digit_hab_user digit_hab_crm_prod
```

---

## 🔐 Sécurité

### Checklist de Sécurité

- [ ] Firewall activé (UFW)
- [ ] SSH sécurisé (désactiver root login)
- [ ] Certificats SSL valides
- [ ] SECRET_KEY unique et sécurisée
- [ ] DEBUG=False
- [ ] Mots de passe forts pour PostgreSQL et Redis
- [ ] ALLOWED_HOSTS configuré correctement
- [ ] CORS_ALLOWED_ORIGINS restrictif
- [ ] Backups automatiques configurés
- [ ] Monitoring en place
- [ ] Logs rotatés
- [ ] Updates système régulières

### Améliorer la Sécurité SSH

```bash
# Éditer la config SSH
sudo nano /etc/ssh/sshd_config

# Désactiver le login root
PermitRootLogin no

# Utiliser seulement des clés SSH
PasswordAuthentication no

# Redémarrer SSH
sudo systemctl restart sshd
```

---

## 📚 Ressources

- **Docker Documentation**: https://docs.docker.com/
- **Django Deployment**: https://docs.djangoproject.com/en/4.2/howto/deployment/
- **Let's Encrypt**: https://letsencrypt.org/
- **Nginx Documentation**: https://nginx.org/en/docs/

---

## ✅ Checklist de Déploiement

### Avant le Déploiement

- [ ] VPS configuré et accessible via SSH
- [ ] Domaine pointant vers l'IP du VPS
- [ ] Docker et Docker Compose installés
- [ ] Certificats SSL générés
- [ ] Variables d'environnement configurées (.env.prod)
- [ ] Fichiers sensibles sécurisés (SECRET_KEY, passwords)

### Pendant le Déploiement

- [ ] Code transféré sur le VPS
- [ ] Docker images buildées
- [ ] Services démarrés (docker compose up -d)
- [ ] Migrations appliquées
- [ ] Statiques collectés
- [ ] Superuser créé

### Après le Déploiement

- [ ] Application accessible via HTTPS
- [ ] Admin Django fonctionne
- [ ] API répond correctement
- [ ] Celery traite les tâches
- [ ] Backups automatiques configurés
- [ ] Monitoring en place
- [ ] Documentation à jour

---

**🎉 Félicitations ! Votre application DIGIT-HAB CRM est déployée !**

*Pour toute question : support@digit-hab.com*
