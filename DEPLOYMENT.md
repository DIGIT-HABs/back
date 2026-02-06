# 🚀 Guide de Déploiement Automatique DIGIT-HAB CRM

Ce guide explique comment configurer le déploiement automatique sur votre serveur de production à chaque merge sur la branche `main`.

## 📋 Table des matières

1. [Prérequis](#prérequis)
2. [Configuration des Secrets GitHub](#configuration-des-secrets-github)
3. [Configuration du Serveur](#configuration-du-serveur)
4. [Déploiement](#déploiement)
5. [Dépannage](#dépannage)

---

## 🔧 Prérequis

### Sur votre serveur de production

- Ubuntu/Debian Linux
- Docker et Docker Compose installés
- Git installé
- Nginx configuré (optionnel, si utilisation de reverse proxy)
- Accès SSH avec clé publique/privée

### Sur GitHub

- Accès administrateur au dépôt
- Possibilité d'ajouter des secrets au dépôt

---

## 🔐 Configuration des Secrets GitHub

### 1. Générer une clé SSH pour le déploiement

Sur votre machine locale ou serveur :

```bash
# Générer une nouvelle clé SSH dédiée au déploiement
ssh-keygen -t ed25519 -C "github-deploy@digit-hab" -f ~/.ssh/github_deploy_key

# Afficher la clé privée (à copier dans GitHub)
cat ~/.ssh/github_deploy_key

# Afficher la clé publique (à ajouter au serveur)
cat ~/.ssh/github_deploy_key.pub
```

### 2. Ajouter la clé publique au serveur

Sur votre serveur de production :

```bash
# Se connecter au serveur
ssh votre-user@votre-serveur

# Ajouter la clé publique aux clés autorisées
echo "VOTRE_CLE_PUBLIQUE" >> ~/.ssh/authorized_keys

# Vérifier les permissions
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### 3. Configurer les secrets dans GitHub

Aller sur GitHub : **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Ajouter les secrets suivants :

| Secret Name | Description | Exemple |
|------------|-------------|---------|
| `SSH_PRIVATE_KEY` | Clé privée SSH pour se connecter au serveur | Contenu de `~/.ssh/github_deploy_key` |
| `SERVER_HOST` | Adresse IP ou nom de domaine du serveur | `123.45.67.89` ou `digit-hab.altoppe.sn` |
| `SERVER_USER` | Nom d'utilisateur SSH | `root` ou `ubuntu` |
| `HEALTH_CHECK_URL` | URL pour vérifier la santé de l'application | `https://api.digit-hab.altoppe.sn/health/` |

### 4. Exemple de configuration des secrets

```plaintext
SSH_PRIVATE_KEY:
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
...
-----END OPENSSH PRIVATE KEY-----

SERVER_HOST:
123.45.67.89

SERVER_USER:
root

HEALTH_CHECK_URL:
https://api.digit-hab.altoppe.sn/health/
```

---

## 🖥️ Configuration du Serveur

### 1. Préparer le répertoire du projet

```bash
# Créer le répertoire si nécessaire
sudo mkdir -p /var/www/digit-hab-crm

# Donner les permissions appropriées
sudo chown -R $USER:$USER /var/www/digit-hab-crm

# Cloner le dépôt (première fois uniquement)
cd /var/www
git clone https://github.com/VOTRE-USERNAME/DIGIT-HAB_CRM_ digit-hab-crm
cd digit-hab-crm
```

### 2. Rendre le script de déploiement exécutable

```bash
chmod +x Django/deploy-final.sh
```

### 3. Créer les répertoires nécessaires

```bash
# Répertoire de backup
sudo mkdir -p /var/backups/digit-hab-crm
sudo chown -R $USER:$USER /var/backups/digit-hab-crm

# Répertoires pour les fichiers statiques et médias
mkdir -p staticfiles media
```

### 4. Configurer les variables d'environnement

Créer le fichier `.env.prod` dans le répertoire `Django/` :

```bash
cd /var/www/digit-hab-crm/Django
nano .env.prod
```

Contenu du fichier `.env.prod` :

```env
# Django
DJANGO_SETTINGS_MODULE=digit_hab_crm.settings.prod
SECRET_KEY=votre-secret-key-super-securisee
DEBUG=False
ALLOWED_HOSTS=api.digit-hab.altoppe.sn,digit-hab.altoppe.sn

# Database
DB_NAME=digit_hab_crm
DB_USER=postgres
DB_PASSWORD=votre-password-db-securise
DB_HOST=db
DB_PORT=5432

# Email (optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-password-email

# Stripe (si utilisé)
STRIPE_PUBLIC_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx

# CORS
CORS_ALLOWED_ORIGINS=https://digit-hab.altoppe.sn
```

### 5. Créer un endpoint de santé (health check)

Ajouter dans `Django/digit_hab_crm/urls.py` :

```python
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok", "message": "Application is running"})

urlpatterns = [
    # ... autres URLs
    path('health/', health_check, name='health-check'),
]
```

---

## 🚀 Déploiement

### Déploiement automatique

Le déploiement se fait automatiquement à chaque merge sur `main` :

1. Faites vos modifications sur une branche de développement
2. Créez une Pull Request vers `main`
3. Une fois la PR approuvée et mergée, le déploiement démarre automatiquement
4. Suivez le déploiement dans l'onglet **Actions** de GitHub

### Déploiement manuel

Vous pouvez aussi déclencher un déploiement manuellement :

1. Allez dans **Actions** sur GitHub
2. Sélectionnez le workflow "🚀 Deploy to Production"
3. Cliquez sur **Run workflow**
4. Sélectionnez la branche `main`
5. Cliquez sur **Run workflow**

### Déploiement direct sur le serveur

Si vous préférez déployer directement depuis le serveur :

```bash
# Se connecter au serveur
ssh votre-user@votre-serveur

# Naviguer vers le projet
cd /var/www/digit-hab-crm

# Exécuter le script de déploiement
./Django/deploy-final.sh
```

---

## 🔍 Vérification du Déploiement

Après le déploiement, vérifiez que tout fonctionne :

### 1. Vérifier les services Docker

```bash
cd /var/www/digit-hab-crm
docker compose -f Django/docker-compose.prod.yml ps
```

Tous les services doivent être "Up" :
- ✅ web
- ✅ db
- ✅ nginx (si utilisé)

### 2. Vérifier les logs

```bash
# Logs de l'application
docker compose -f Django/docker-compose.prod.yml logs -f web

# Logs de la base de données
docker compose -f Django/docker-compose.prod.yml logs -f db
```

### 3. Tester les endpoints

```bash
# Test de santé
curl https://api.digit-hab.altoppe.sn/health/

# Test de l'API
curl https://api.digit-hab.altoppe.sn/api/

# Test de l'admin
curl -I https://api.digit-hab.altoppe.sn/admin/
```

### 4. Vérifier dans le navigateur

- 🌐 Admin : https://api.digit-hab.altoppe.sn/admin/
- 🌐 API : https://api.digit-hab.altoppe.sn/api/
- 🌐 Docs : https://api.digit-hab.altoppe.sn/api/docs/

---

## 🛠️ Dépannage

### Problème : Le déploiement échoue avec une erreur SSH

**Solution :**
1. Vérifiez que la clé privée SSH est correctement configurée dans GitHub Secrets
2. Assurez-vous que la clé publique est dans `~/.ssh/authorized_keys` sur le serveur
3. Vérifiez les permissions : `chmod 600 ~/.ssh/authorized_keys`

### Problème : Les conteneurs Docker ne démarrent pas

**Solution :**
```bash
# Voir les logs détaillés
docker compose -f Django/docker-compose.prod.yml logs

# Reconstruire les images
docker compose -f Django/docker-compose.prod.yml build --no-cache

# Redémarrer les services
docker compose -f Django/docker-compose.prod.yml up -d
```

### Problème : Erreur 502 Bad Gateway

**Solution :**
1. Vérifiez que le conteneur web est en cours d'exécution
2. Vérifiez les logs : `docker compose logs web`
3. Vérifiez la configuration Nginx
4. Redémarrez les services : `docker compose restart`

### Problème : Base de données inaccessible

**Solution :**
```bash
# Vérifier que PostgreSQL fonctionne
docker compose -f Django/docker-compose.prod.yml exec db psql -U postgres -c "SELECT 1"

# Restaurer depuis un backup si nécessaire
cat /var/backups/digit-hab-crm/db_backup_YYYYMMDD_HHMMSS.sql | \
  docker compose -f Django/docker-compose.prod.yml exec -T db psql -U postgres digit_hab_crm
```

### Problème : Migrations de base de données échouent

**Solution :**
```bash
# Voir l'état des migrations
docker compose -f Django/docker-compose.prod.yml exec web python manage.py showmigrations

# Appliquer les migrations manuellement
docker compose -f Django/docker-compose.prod.yml exec web python manage.py migrate

# En cas de conflit, créer un snapshot
docker compose -f Django/docker-compose.prod.yml exec web python manage.py makemigrations --merge
```

---

## 📊 Monitoring et Maintenance

### Voir les logs en temps réel

```bash
docker compose -f Django/docker-compose.prod.yml logs -f web
```

### Redémarrer l'application

```bash
docker compose -f Django/docker-compose.prod.yml restart web
```

### Voir l'utilisation des ressources

```bash
docker stats
```

### Nettoyer les anciennes images

```bash
docker system prune -a
```

### Backups automatiques

Les backups de la base de données sont créés automatiquement lors de chaque déploiement dans :
```
/var/backups/digit-hab-crm/db_backup_YYYYMMDD_HHMMSS.sql
```

Les 10 derniers backups sont conservés automatiquement.

---

## 📞 Support

Pour toute question ou problème :

1. Vérifiez les logs de l'application
2. Consultez la documentation Django
3. Vérifiez les issues GitHub du projet
4. Contactez l'équipe de développement

---

## ✅ Checklist de Déploiement

Avant de déployer en production :

- [ ] Les secrets GitHub sont configurés
- [ ] La clé SSH fonctionne
- [ ] Le fichier `.env.prod` est configuré sur le serveur
- [ ] Les migrations sont à jour
- [ ] Les tests passent
- [ ] La configuration Nginx est correcte
- [ ] Les certificats SSL sont valides
- [ ] Un backup récent existe
- [ ] L'équipe est prévenue du déploiement

---

**Dernière mise à jour :** Février 2026  
**Version :** 1.0
