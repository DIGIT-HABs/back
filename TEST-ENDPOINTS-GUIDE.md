# 🧪 GUIDE DE TEST DES NOUVEAUX ENDPOINTS

**Phase 1 : Fondations**  
**Date :** Janvier 2025

---

## 📋 PRÉREQUIS

1. ✅ Serveur Django démarré : `python manage.py runserver`
2. ✅ Migrations appliquées : `python manage.py migrate`
3. ✅ Utilisateur agent créé dans la base de données
4. ✅ Package `requests` installé : `pip install requests`

---

## 🚀 MÉTHODE 1 : Script Automatique

### Exécution

```bash
cd Django
python test_new_endpoints.py
```

### Ce que teste le script

**Endpoints Clients (5 tests) :**
- ✅ `GET /api/crm/clients/` - Liste clients
- ✅ `GET /api/crm/clients/{id}/interactions/` - Historique interactions
- ✅ `POST /api/crm/clients/{id}/interactions/` - Ajouter interaction
- ✅ `GET /api/crm/clients/{id}/stats/` - Statistiques client
- ✅ `POST /api/crm/clients/{id}/contact/` - Action contact

**Endpoints Leads (3 tests) :**
- ✅ `GET /api/crm/leads/` - Liste leads
- ✅ `POST /api/crm/leads/{id}/qualify/` - Qualifier lead
- ✅ `GET /api/crm/leads/pipeline/` - Vue pipeline

**Endpoints Commissions (6 tests) :**
- ✅ `GET /api/commissions/commissions/` - Liste commissions
- ✅ `POST /api/commissions/commissions/` - Créer commission
- ✅ `GET /api/commissions/commissions/stats/` - Statistiques
- ✅ `GET /api/commissions/commissions/pending/` - En attente
- ✅ `GET /api/commissions/payments/` - Liste paiements
- ✅ `GET /api/commissions/payments/history/` - Historique

**Total : 14 tests**

---

## 🌐 MÉTHODE 2 : Swagger UI (Interface Graphique)

### Accès

```
http://localhost:8000/api/docs/
```

### Tests Manuels

1. **Authentification**
   - Cliquer sur `/api/auth/login/`
   - Entrer email/password
   - Copier le `access` token
   - Cliquer sur "Authorize" (cadenas en haut)
   - Coller : `Bearer {token}`

2. **Tester chaque endpoint**
   - Cliquer sur l'endpoint
   - Cliquer "Try it out"
   - Remplir les paramètres
   - Cliquer "Execute"
   - Vérifier la réponse

---

## 📝 MÉTHODE 3 : Postman / Insomnia

### Collection Postman

Créer une collection avec les endpoints suivants :

#### Authentification
```
POST http://localhost:8000/api/auth/login/
Body (JSON):
{
  "email": "agent@example.com",
  "password": "password123"
}
```

#### Clients
```
GET http://localhost:8000/api/crm/clients/
GET http://localhost:8000/api/crm/clients/{id}/
GET http://localhost:8000/api/crm/clients/{id}/interactions/
POST http://localhost:8000/api/crm/clients/{id}/add_interaction/
GET http://localhost:8000/api/crm/clients/{id}/stats/
POST http://localhost:8000/api/crm/clients/{id}/contact/
```

#### Leads
```
GET http://localhost:8000/api/crm/leads/
POST http://localhost:8000/api/crm/leads/
POST http://localhost:8000/api/crm/leads/{id}/qualify/
GET http://localhost:8000/api/crm/leads/pipeline/
```

#### Commissions
```
GET http://localhost:8000/api/commissions/commissions/
POST http://localhost:8000/api/commissions/commissions/
GET http://localhost:8000/api/commissions/commissions/stats/
GET http://localhost:8000/api/commissions/commissions/pending/
GET http://localhost:8000/api/commissions/payments/
GET http://localhost:8000/api/commissions/payments/history/
```

---

## 🔍 EXEMPLES DE REQUÊTES

### 1. Ajouter Interaction Client

```bash
curl -X POST "http://localhost:8000/api/crm/clients/{client_id}/add_interaction/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "{agent_id}",
    "interaction_type": "call",
    "channel": "phone",
    "subject": "Appel de suivi",
    "content": "Client intéressé par la propriété",
    "priority": "medium",
    "status": "scheduled"
  }'
```

### 2. Qualifier un Lead

```bash
curl -X POST "http://localhost:8000/api/crm/leads/{lead_id}/qualify/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "qualification": "hot",
    "notes": "Lead très intéressé, budget confirmé"
  }'
```

### 3. Créer une Commission

```bash
curl -X POST "http://localhost:8000/api/commissions/commissions/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "{agent_id}",
    "agency_id": "{agency_id}",
    "commission_type": "sale",
    "base_amount": "100000000",
    "commission_rate": "3.00",
    "status": "pending",
    "notes": "Commission vente villa"
  }'
```

### 4. Pipeline Leads

```bash
curl -X GET "http://localhost:8000/api/crm/leads/pipeline/" \
  -H "Authorization: Bearer {token}"
```

---

## ✅ CHECKLIST DE VALIDATION

### Endpoints Clients
- [ ] Liste clients retourne 200 OK
- [ ] Interactions client retourne liste
- [ ] Ajouter interaction crée l'interaction
- [ ] Stats client retourne données
- [ ] Contact client crée interaction

### Endpoints Leads
- [ ] Liste leads retourne 200 OK
- [ ] Qualifier lead met à jour qualification
- [ ] Pipeline retourne structure Kanban

### Endpoints Commissions
- [ ] Liste commissions retourne 200 OK
- [ ] Créer commission calcule montant
- [ ] Stats retourne métriques
- [ ] Pending retourne commissions en attente
- [ ] Liste paiements retourne 200 OK
- [ ] Historique retourne paiements complétés

---

## 🐛 DÉPANNAGE

### Erreur 401 (Unauthorized)
- Vérifier que le token est valide
- Vérifier le format : `Bearer {token}`
- Se reconnecter si token expiré

### Erreur 403 (Forbidden)
- Vérifier que l'utilisateur a le rôle `agent` ou `admin`
- Vérifier les permissions dans le code

### Erreur 404 (Not Found)
- Vérifier que l'ID existe dans la base
- Vérifier l'URL de l'endpoint

### Erreur 400 (Bad Request)
- Vérifier le format JSON
- Vérifier les champs requis
- Vérifier les types de données

---

## 📊 RÉSULTATS ATTENDUS

### Succès
```
✅ Tests réussis : 14
❌ Tests échoués : 0
⏭️  Tests ignorés : 0
```

### Si erreurs
- Vérifier les logs Django
- Vérifier la base de données
- Vérifier les migrations
- Vérifier les permissions

---

**🎯 Objectif : Tous les endpoints doivent retourner 200 OK ou 201 Created**
