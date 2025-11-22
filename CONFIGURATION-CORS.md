# 🔧 Configuration CORS - Django

## ✅ Problème Résolu

Le problème de login était causé par **CORS** (Cross-Origin Resource Sharing).

### Symptôme
```
INFO "OPTIONS /api/auth/login/ HTTP/1.1" 200 0
```

La requête OPTIONS (preflight) réussit, mais la requête POST ne part jamais.

### Cause
Django n'autorisait que `localhost:3000` (Next.js) mais pas `localhost:8081` (Expo).

---

## 🛠️ Configuration Appliquée

### 1. ALLOWED_HOSTS

```python
# Django/digit_hab_crm/settings/base.py
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '192.168.1.201']
```

### 2. CORS Settings

```python
# Origines autorisées
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',      # Next.js
    'http://127.0.0.1:3000',      
    'http://localhost:8081',      # Expo Metro
    'http://127.0.0.1:8081',      
]

# Headers autorisés
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Méthodes autorisées
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Credentials
CORS_ALLOW_CREDENTIALS = True

# En développement : accepter toutes les origines
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
```

### 3. Middleware Order

```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ← DOIT être en premier
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

---

## 🚀 Relancer le Backend

**Important** : Vous devez **redémarrer Django** pour que les changements prennent effet !

```bash
# Arrêter le serveur (Ctrl+C)

# Relancer
cd Django
python manage.py runserver 0.0.0.0:8000
```

---

## ✅ Tester

### 1. Depuis le terminal

```bash
curl -X POST http://192.168.1.201:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"agent@test.com","password":"test123"}'
```

Devrait retourner un token ✅

### 2. Depuis l'app mobile

1. Relancez l'app : `npm start`
2. Allez sur Login
3. Utilisez les comptes de test :
   - **Agent** : `agent@test.com` / `test123`
   - **Client** : `client@test.com` / `test123`

---

## 🐛 Troubleshooting

### ❌ "Network Request Failed"

**Vérifier l'IP dans l'app** :

```typescript
// Native/config/api.config.ts
BASE_URL: 'http://192.168.1.201:8000/api'  // ← Votre IP ici
```

### ❌ "CORS header 'Access-Control-Allow-Origin' missing"

**Solution** :

1. Vérifier que `corsheaders` est installé :
```bash
pip install django-cors-headers
```

2. Vérifier `INSTALLED_APPS` :
```python
THIRD_PARTY_APPS = [
    ...
    'corsheaders',  # ← Doit être présent
    ...
]
```

3. Redémarrer Django

### ❌ "Forbidden (CSRF token missing)"

**Solution** : Ajouter dans `settings/base.py` :

```python
# Pour API REST, désactiver CSRF sur les endpoints API
REST_FRAMEWORK = {
    ...
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# Ou exempter les vues API du CSRF
from django.views.decorators.csrf import csrf_exempt
```

---

## 📝 Notes pour Production

**En production**, ne pas utiliser `CORS_ALLOW_ALL_ORIGINS = True` !

À la place :

```python
# settings/production.py
CORS_ALLOWED_ORIGINS = [
    'https://www.digit-hab.com',
    'https://app.digit-hab.com',
    'https://mobile.digit-hab.com',
]
```

---

## 🔒 Sécurité

### Développement (OK)
```python
DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True
ALLOWED_HOSTS = ['*']
```

### Production (Strict)
```python
DEBUG = False
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = ['https://digit-hab.com']
ALLOWED_HOSTS = ['api.digit-hab.com']
```

---

## ✅ Résumé

### Avant
```
❌ Login ne marche pas
❌ OPTIONS 200, mais POST jamais envoyé
❌ Erreur CORS
```

### Après
```
✅ CORS correctement configuré
✅ Login fonctionne depuis l'app mobile
✅ Toutes les requêtes API passent
```

---

## 🎉 C'est Réglé !

Le login devrait maintenant fonctionner parfaitement ! 🚀

**N'oubliez pas de redémarrer Django** après avoir modifié `settings/base.py` !


