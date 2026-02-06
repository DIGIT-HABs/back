# 🚀 GitHub Actions Workflows

<!-- test -->

Ce dossier contient les workflows GitHub Actions pour l'automatisation du déploiement.

## Workflows disponibles

### 📦 Deploy to Production (`deploy.yml`)

Déploie automatiquement l'application sur le serveur de production.

**Déclenchement :**
- ✅ Automatique : À chaque push/merge sur la branche `main`
- ✅ Manuel : Via l'interface GitHub Actions

**Conditions :**
- Modifications dans le dossier `Django/`
- Modifications du workflow lui-


**Étapes :**
1. Récupération du code
2. Configuration SSH
3. Connexion au serveur
4. Exécution du script de déploiement
5. Health check
6. Notifications

## 🔐 Configuration requise

### Secrets GitHub nécessaires

Configurez ces secrets dans : **Settings** → **Secrets and variables** → **Actions**

| Secret | Description |
|--------|-------------|
| `SSH_PRIVATE_KEY` | Clé privée SSH pour accéder au serveur |
| `SERVER_HOST` | IP ou domaine du serveur (ex: `123.45.67.89`) |
| `SERVER_USER` | Utilisateur SSH (ex: `root`) |
| `HEALTH_CHECK_URL` | URL de santé (ex: `https://api.digit-hab.altoppe.sn/health/`) |

## 📋 Guide rapide

### 1. Configuration initiale (une seule fois)

```bash
# 1. Générer une clé SSH
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy_key

# 2. Copier la clé privée dans GitHub Secrets (SSH_PRIVATE_KEY)
cat ~/.ssh/github_deploy_key

# 3. Ajouter la clé publique au serveur
ssh-copy-id -i ~/.ssh/github_deploy_key.pub user@serveur
```

### 2. Déploiement automatique

```bash
# Sur votre branche de développement
git add .
git commit -m "Nouvelle fonctionnalité"
git push origin ma-branche

# Créer une Pull Request vers main
# Une fois mergée → Déploiement automatique ! 🚀
```

### 3. Déploiement manuel

1. Aller sur GitHub → **Actions**
2. Sélectionner "🚀 Deploy to Production"
3. Cliquer sur **Run workflow**
4. Sélectionner la branche `main`
5. Cliquer sur **Run workflow**

## 📊 Suivi du déploiement

### Voir le statut

- Onglet **Actions** sur GitHub
- Badge de statut dans le README (à ajouter)
- Notifications par email

### Logs en temps réel

Pendant le déploiement, vous pouvez voir :
- Les étapes en cours
- Les logs de chaque étape
- Le résultat du health check
- Le résumé du déploiement

## 🛠️ Personnalisation

### Modifier le workflow

Éditez `.github/workflows/deploy.yml` pour :
- Changer les conditions de déclenchement
- Ajouter des étapes de test
- Modifier les notifications
- Ajouter des vérifications post-déploiement

### Ajouter des tests avant déploiement

```yaml
jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          cd Django
          python -m pytest

  deploy:
    needs: test  # Déploie seulement si les tests passent
    name: Deploy to Production
    # ... reste du workflow
```

## 📚 Documentation complète

Pour plus de détails, consultez : [Django/DEPLOYMENT.md](../../Django/DEPLOYMENT.md)

## ⚠️ Important

- **Ne jamais commiter de secrets** dans le code
- Toujours tester sur un environnement de staging avant production
- Faire des backups avant chaque déploiement (automatique dans le script)
- Vérifier les logs après chaque déploiement

## 🔗 Liens utiles

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Deploying with SSH](https://github.com/marketplace/actions/ssh-remote-commands)
- [Docker Compose in Production](https://docs.docker.com/compose/production/)

---

**Besoin d'aide ?** Consultez [DEPLOYMENT.md](../../Django/DEPLOYMENT.md) ou contactez l'équipe DevOps.
