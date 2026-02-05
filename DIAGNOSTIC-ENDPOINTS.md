# 🔍 DIAGNOSTIC DES ENDPOINTS - GUIDE

**Date :** Janvier 2025  
**Problème :** 3 endpoints retournent "No response"

---

## ❌ PROBLÈMES IDENTIFIÉS

### Endpoints qui échouent :
1. `GET /api/crm/leads/` - No response
2. `GET /api/crm/leads/pipeline/` - No response
3. `POST /api/commissions/commissions/` - No response

---

## ✅ CORRECTIONS APPLIQUÉES

### 1. Compatibilité SQLite pour DATE_TRUNC ✅

**Problème :** `DATE_TRUNC` est une fonction PostgreSQL uniquement, mais la base est SQLite.

**Fichier :** `Django/apps/commissions/views.py`

**Solution :** Détection automatique du type de base de données :
- SQLite : utilise `strftime('%Y-%m', transaction_date)`
- PostgreSQL : utilise `DATE_TRUNC('month', transaction_date)`

### 2. Amélioration messages d'erreur ✅

**Fichier :** `Django/test_new_endpoints.py`

**Améliorations :**
- Messages d'erreur plus détaillés
- Affichage du code de statut HTTP
- Affichage de la réponse en cas d'erreur
- Détection des erreurs serveur (500)

---

## 🔍 DIAGNOSTIC ÉTAPE PAR ÉTAPE

### Étape 1 : Vérifier que le serveur est démarré

```bash
# Dans un terminal
cd Django
python manage.py runserver
```

**Vérifier :** Le serveur doit afficher :
```
Starting development server at http://127.0.0.1:8000/
```

### Étape 2 : Tester avec le script simple

```bash
python test_simple_endpoint.py
```

Ce script teste chaque endpoint individuellement et affiche l'erreur exacte.

### Étape 3 : Vérifier les logs Django

Si le serveur est démarré, regardez les logs dans le terminal où Django tourne.

**Erreurs possibles :**
- `AttributeError` : Problème avec un attribut
- `DoesNotExist` : Objet non trouvé
- `ValidationError` : Erreur de validation
- `DatabaseError` : Erreur SQL

### Étape 4 : Tester manuellement avec curl

```bash
# 1. Se connecter
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"moussa.diop@digit-hab.com","password":"test123"}'

# Copier le token

# 2. Tester endpoint leads
curl -X GET http://localhost:8000/api/crm/leads/ \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json"
```

---

## 🐛 CAUSES POSSIBLES DE "NO RESPONSE"

### 1. Serveur Django non démarré
**Symptôme :** `ConnectionError`  
**Solution :** Démarrer le serveur

### 2. Erreur dans le code qui fait planter le serveur
**Symptôme :** Le serveur plante quand on appelle l'endpoint  
**Solution :** Vérifier les logs Django

### 3. Timeout
**Symptôme :** La requête prend trop de temps  
**Solution :** Vérifier les requêtes SQL (peut-être trop lentes)

### 4. Erreur de validation
**Symptôme :** 400 Bad Request  
**Solution :** Vérifier les données envoyées

### 5. Erreur serveur (500)
**Symptôme :** 500 Internal Server Error  
**Solution :** Vérifier les logs Django pour l'erreur exacte

---

## 🔧 ACTIONS CORRECTIVES

### Si le serveur plante

1. **Vérifier les logs Django** dans le terminal
2. **Chercher l'erreur** (AttributeError, DoesNotExist, etc.)
3. **Corriger le code** selon l'erreur

### Si erreur 500

1. **Vérifier les logs Django**
2. **Vérifier la stack trace**
3. **Corriger le problème identifié**

### Si erreur 400

1. **Vérifier les données envoyées**
2. **Vérifier les validations dans les serializers**
3. **Vérifier les permissions**

---

## 📝 CHECKLIST DE DIAGNOSTIC

- [ ] Serveur Django démarré ?
- [ ] Token JWT valide ?
- [ ] Utilisateur a le rôle `agent` ou `admin` ?
- [ ] Utilisateur a une agence associée ?
- [ ] Base de données accessible ?
- [ ] Migrations appliquées ?
- [ ] Logs Django vérifiés ?

---

## 🚀 PROCHAINES ÉTAPES

1. **Démarrer le serveur Django** (si pas déjà fait)
2. **Exécuter le script de diagnostic** : `python test_simple_endpoint.py`
3. **Vérifier les logs Django** pour voir les erreurs exactes
4. **Corriger les erreurs** identifiées
5. **Relancer les tests complets** : `python test_new_endpoints.py`

---

**💡 Le script `test_simple_endpoint.py` vous donnera l'erreur exacte pour chaque endpoint !**
