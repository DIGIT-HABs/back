# ✅ Checklist de Déploiement DIGIT-HAB CRM

## 📋 Avant le Déploiement

### VPS & Infrastructure
- [ ] VPS loué et accessible (2 vCPUs, 4GB RAM minimum)
- [ ] Ubuntu 22.04 LTS installé
- [ ] Accès SSH configuré (root ou sudo user)
- [ ] IP publique fixe obtenue
- [ ] Domaine acheté (digit-hab.com)
- [ ] DNS configuré pointant vers l'IP du VPS

### Sécurité
- [ ] Firewall UFW installé et configuré
- [ ] Ports 22, 80, 443 ouverts
- [ ] Utilisateur non-root créé (digit-hab)
- [ ] Clés SSH configurées (désactiver password auth recommandé)

### Logiciels
- [ ] Docker installé (version 20.10+)
- [ ] Docker Compose installé (version 2.x)
- [ ] Git installé
- [ ] Certbot installé (pour SSL)

---

## 🔧 Configuration

### Fichiers de Configuration
- [ ] `.env` créé et rempli avec valeurs production
- [ ] `SECRET_KEY` générée (unique et sécurisée)
- [ ] `DEBUG=False` défini
- [ ] `ALLOWED_HOSTS` correctement configuré
- [ ] Mots de passe PostgreSQL et Redis forts définis
- [ ] Credentials email/Cloudinary/Stripe mis à jour
- [ ] `CORS_ALLOWED_ORIGINS` restrictif

### SSL/HTTPS
- [ ] Certificats Let's Encrypt générés
- [ ] Certificats copiés dans `./ssl/`
- [ ] nginx.prod.conf configuré avec les bons domaines
- [ ] Renouvellement automatique configuré (cron)

### Fichiers Docker
- [ ] `Dockerfile` vérifié
- [ ] `docker-compose.yml` vérifié
- [ ] `nginx.prod.conf` vérifié
- [ ] `.dockerignore` créé (si nécessaire)

---

## 🚀 Déploiement

### Transfert du Code
- [ ] Code transféré sur VPS (git clone ou scp)
- [ ] Fichiers dans `/home/digit-hab/DIGIT-HAB_CRM/Django/`
- [ ] Permissions correctes sur les fichiers

### Build & Start
- [ ] `docker compose build` exécuté sans erreur
- [ ] `docker compose up -d` exécuté
- [ ] Tous les services démarrés (db, redis, web, celery, nginx)
- [ ] `docker compose ps` montre tous services "Up"

### Base de Données
- [ ] Migrations appliquées (`docker compose exec web python manage.py migrate`)
- [ ] Superuser créé (`docker compose exec web python manage.py createsuperuser`)
- [ ] Données de test créées (optionnel)

### Fichiers Statiques
- [ ] `collectstatic` exécuté
- [ ] Fichiers statiques accessibles via nginx
- [ ] Dossiers `staticfiles/` et `media/` créés

---

## ✅ Tests Post-Déploiement

### Accès de Base
- [ ] Site accessible via HTTP: `http://digit-hab.com`
- [ ] Redirection HTTPS fonctionne
- [ ] Site accessible via HTTPS: `https://digit-hab.com`
- [ ] Pas d'erreur de certificat SSL
- [ ] Sous-domaines fonctionnent (api.digit-hab.com, www.digit-hab.com)

### Endpoints Principaux
- [ ] Health check: `https://digit-hab.com/health/` → 200 OK
- [ ] Admin Django: `https://digit-hab.com/admin/` accessible
- [ ] API: `https://digit-hab.com/api/` répond
- [ ] API Docs: `https://digit-hab.com/api/docs/` accessible

### Fonctionnalités
- [ ] Login admin fonctionne
- [ ] Création d'un client via admin fonctionne
- [ ] API clients retourne des données: `/api/crm/clients/`
- [ ] Upload d'image fonctionne (media)
- [ ] Fichiers statiques chargent (CSS, JS)

### Services Backend
- [ ] PostgreSQL fonctionne (connexion DB OK)
- [ ] Redis fonctionne (`docker compose exec redis redis-cli ping`)
- [ ] Celery worker traite les tâches
- [ ] Celery beat schedule fonctionne
- [ ] Logs accessibles sans erreurs critiques

### Performance & Sécurité
- [ ] Headers de sécurité présents (HSTS, X-Frame-Options, etc.)
- [ ] CORS configuré correctement
- [ ] Rate limiting fonctionne
- [ ] Gzip compression active
- [ ] Temps de réponse acceptable (< 2s)

---

## 🔄 Post-Déploiement

### Monitoring & Logs
- [ ] Logs Docker accessibles: `docker compose logs -f`
- [ ] Dossier `logs/` créé
- [ ] Log rotation configurée
- [ ] ctop installé pour monitoring

### Backups
- [ ] Script de backup créé (`~/backup-digit-hab.sh`)
- [ ] Cron job backup configuré (quotidien)
- [ ] Dossier backups créé (`~/backups/`)
- [ ] Test de backup effectué
- [ ] Test de restore effectué

### Maintenance
- [ ] Procédure de mise à jour documentée
- [ ] Accès d'urgence configuré
- [ ] Contacts support définis
- [ ] Documentation à jour

---

## 🛡️ Sécurité Production

### Configurations Django
- [ ] `DEBUG=False` ✅ CRITIQUE
- [ ] `SECRET_KEY` unique et forte
- [ ] `ALLOWED_HOSTS` restrictif
- [ ] `SECURE_SSL_REDIRECT=True`
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] `CSRF_COOKIE_SECURE=True`
- [ ] `SECURE_HSTS_SECONDS` configuré

### Configurations Serveur
- [ ] Firewall UFW actif
- [ ] Fail2ban installé (optionnel mais recommandé)
- [ ] SSH sécurisé (no root login, key-based auth)
- [ ] Mots de passe forts partout
- [ ] Credentials ne sont PAS dans Git

### Réseau & SSL
- [ ] Certificats SSL valides
- [ ] HTTPS forcé (redirect 80→443)
- [ ] TLS 1.2+ uniquement
- [ ] Ciphers sécurisés configurés

---

## 📊 Métriques de Succès

### Performance
- [ ] Temps de réponse API < 500ms
- [ ] Temps de chargement page < 2s
- [ ] Uptime > 99.5%
- [ ] CPU usage < 70%
- [ ] RAM usage < 80%
- [ ] Disk usage < 80%

### Fonctionnel
- [ ] Toutes les pages chargent sans erreur 500
- [ ] Aucune erreur dans les logs
- [ ] Toutes les fonctionnalités CRM testées
- [ ] Emails envoyés correctement
- [ ] Paiements Stripe fonctionnent (si activé)
- [ ] Upload fichiers fonctionne

---

## 🚨 Plan de Rollback

### En Cas de Problème

1. **Problème Critique** :
   ```bash
   cd ~/DIGIT-HAB_CRM/Django
   docker compose down
   git checkout DERNIERE_VERSION_STABLE
   docker compose up -d
   ```

2. **Problème Base de Données** :
   ```bash
   # Restaurer depuis backup
   cat ~/backups/db_DERNIERE_DATE.sql | \
     docker compose exec -T db psql -U digit_hab_user digit_hab_crm_prod
   ```

3. **Contact Support** :
   - Email: support@digit-hab.com
   - Backup des logs: `docker compose logs > logs_$(date +%Y%m%d).txt`

---

## 📝 Notes Finales

### Après Premier Déploiement
- [ ] Créer 5-10 clients de test
- [ ] Tester toutes les fonctionnalités principales
- [ ] Vérifier les emails de notification
- [ ] Tester l'export PDF
- [ ] Vérifier les rapports Excel
- [ ] Tester la recherche et les filtres

### Documentation
- [ ] Mettre à jour le README avec l'URL production
- [ ] Documenter les credentials admin
- [ ] Créer guide utilisateur (si nécessaire)
- [ ] Documenter les procédures de maintenance

### Communication
- [ ] Informer l'équipe du déploiement
- [ ] Partager les URL d'accès
- [ ] Former les utilisateurs si nécessaire

---

## ✅ Validation Finale

**Date de déploiement** : _______________  
**Déployé par** : _______________  
**Version** : _______________  

**Signature** : _______________

---

**🎉 Félicitations ! Votre application est en production !**

*Pour toute question, consulter le guide complet VPS.md*
