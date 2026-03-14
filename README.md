# DIGIT-HAB CRM - Documentation

## 📋 **Phase 1 Complétée - Architecture & Authentification**

### ✅ **Ce qui a été créé :**

#### **1. Architecture Django 5 Modulaire**
```
digit_hab_crm/
├── digit_hab_crm/         # Configuration principale
│   ├── settings/          # Settings modulaires (base/dev/prod)
│   ├── urls.py            # URLs principales + API documentation
│   ├── asgi.py           # ASGI configuration
│   └── wsgi.py           # WSGI configuration
├── apps/                  # Modules métier
│   ├── auth/             # 🔐 Authentification & Users
│   └── properties/       # 🏠 Gestion des biens
├── requirements.txt       # Dépendances modernes
├── .env.example          # Configuration environnement
├── docker/               # Configuration Docker (à venir)
└── manage.py            # Gestion Django
```

#### **2. Module Authentification (`apps/auth/`)**
- **Modèles Django :**
  - `User` : Utilisateur personnalisé avec vérifications
  - `Agency` : Agences immobilières avec abonnements
  - `UserProfile` : Profils utilisateurs étendus

- **Fonctionnalités Auth :**
  - ✅ JWT Authentication avec SimpleJWT
  - ✅ Permissions personnalisées
  - ✅ Signaux Django automatiques
  - ✅ Admin Django complet
  - ✅ Serialiseurs DRF complets
  - ✅ Vues API REST complètes

#### **3. Module Properties (`apps/properties/`)**
- **Modèles Django :**
  - `Property` : Biens immobiliers avec géolocalisation
  - `PropertyImage` : Images de biens
  - `PropertyDocument` : Documents de biens
  - `PropertyVisit` : Visites programmées
  - `PropertyHistory` : Historique/audit
  - `PropertySearch` : Recherches sauvegardées

- **Fonctionnalités Properties :**
  - ✅ Support PostGIS (coordonnées géographiques)
  - ✅ Gestion complète des caractéristiques immobilières
  - ✅ Historique des modifications
  - ✅ Système de visites

#### **4. Configuration Technique**
- **Database :** PostgreSQL 15 + PostGIS
- **Cache :** Redis pour sessions et cache
- **API :** Django REST Framework
- **Auth :** JWT avec SimpleJWT
- **Documentation :** Swagger UI avec Spectacular
- **Validation :** Pydantic pour les données
- **Background Tasks :** Celery + Redis
- **Testing :** Pytest configuré

#### **5. Sécurité & Performances**
- ✅ CORS configuré pour frontend
- ✅ Validation robuste des données
- ✅ Permissions granulaires
- ✅ Index de base de données optimisés
- ✅ Cache Redis configuré
- ✅ API Documentation interactive

## 🚀 **Technologies Utilisées**

### **Backend Stack :**
- **Django 5** - Framework web
- **Django REST Framework 3.15** - API REST
- **PostgreSQL 15 + PostGIS** - Base de données géospatiale
- **Redis 5** - Cache et sessions
- **Celery 5** - Tâches asynchrones
- **SimpleJWT** - Authentication JWT
- **Django CORS Headers** - Gestion CORS
- **Django Filters** - Filtrage API
- **Django Spectacular** - Documentation API

### **Development Tools :**
- **Black** - Formatage de code
- **isort** - Import sorting
- **Pytest** - Tests
- **Django Extensions** - Outils de développement
- **Factory Boy** - Factories de test

## 📊 **Diagrammes UML Créés**

Tous les diagrammes de classes et cas d'utilisation sont disponibles dans :
- `diagrams/use_case_digit_hab.png` - Cas d'utilisation
- `diagrams/class_diagram_global.png` - Architecture globale
- `diagrams/class_diagram_properties.png` - Module Properties
- `diagrams/class_diagram_clients.png` - Module CRM (prévu)
- `diagrams/class_diagram_payments.png` - Module Paiements (prévu)
- `diagrams/architecture_overview.png` - Vue technique

## 🛠️ **Commandes de Développement**

### **Installation & Setup :**
```bash
# 1. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configuration environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# 4. Setup base de données
python manage.py migrate --skip-checks
python manage.py create_agency --name="Agence Digit Hab" --email="contact@digit-hab.com"
python manage.py create_agency --name="Agence Digit Hab" --email="contact@digit-hab.com" --password="password"

python manage.py makemigrations
python manage.py migrate

# 5. Créer superutilisateur
python manage.py createsuperuser

# 6. Lancer le serveur
python manage.py runserver 0000
daphne -b 0.0.0.0 -p 8000 digit_hab_crm.asgi:application
```

### **Accès à l'Application :**
- **Admin Django :** http://localhost:8000/admin/
- **API Documentation :** http://localhost:8000/api/docs/
- **API Endpoints :** http://localhost:8000/api/

## 🔗 **API Endpoints Disponibles**

### **Authentification :**
- `POST /api/auth/token/` - Connexion JWT
- `POST /api/auth/token/refresh/` - Rafraîchir token
- `POST /api/auth/logout/` - Déconnexion
- `GET /api/auth/verify/` - Vérifier token
- `GET /api/auth/users/me/` - Profil utilisateur

### **Gestion des Utilisateurs :**
- `GET/POST /api/auth/users/` - Liste/Créer utilisateurs
- `GET/PUT/PATCH/DELETE /api/auth/users/{id}/` - CRUD utilisateur
- `GET/PUT/PATCH /api/auth/profiles/{id}/` - Profils utilisateurs

### **Gestion des Agences :**
- `GET /api/auth/agencies/` - Liste agences
- `GET /api/auth/agencies/{id}/` - Détail agence
- `GET /api/auth/agencies/{id}/statistics/` - Statistiques

### **Gestion des Biens :**
- `GET/POST /api/properties/` - Liste/Créer biens
- `GET/PUT/PATCH/DELETE /api/properties/{id}/` - CRUD bien
- `GET /api/properties/{id}/images/` - Images du bien
- `GET /api/properties/{id}/visits/` - Visites du bien
- `GET /api/properties/{id}/history/` - Historique du bien

## 🔄 **Prochaines Étapes**

### **Phase 2 : Module CRM/Clients (à venir)**
- Modèles Client, Lead, Interaction
- Système de matching client-bien
- Tâches automation (relances, notifications)

### **Phase 3 : Module Réservations (à venir)**
- Système de réservations
- Intégration Stripe
- Signatures électroniques
- Commission calculation
prévoir dès le départ la gestion locative (baux, quittances, régularisation charges) ?

### **Phase 4 : Frontend (à venir)**
- Application web Next.js 14
- Application mobile React Native
- Interface utilisateur moderne

### **Phase 5 : Tâches Avancées (à venir)**
- Notifications push
- Email automation
- Analytics et reporting
- IA/Machine Learning features

## 📞 **Support & Contact**

Pour toute question sur l'architecture ou le développement, n'hésitez pas à me demander des clarifications ou à me proposer des modifications !

**L'architecture modulaire permet un développement parallèle et une scalabilité optimale.**