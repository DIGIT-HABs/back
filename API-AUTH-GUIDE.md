# 🔐 Guide d'Authentification API - DIGIT-HAB CRM

## 📋 Table des matières
- [Endpoints Disponibles](#endpoints-disponibles)
- [Authentification Email + Password](#authentification-email--password)
- [Inscription](#inscription)
- [Google OAuth (V2)](#google-oauth-v2)
- [Apple Sign In (V2)](#apple-sign-in-v2)
- [Exemples d'intégration](#exemples-dintégration)

---

## 🎯 Endpoints Disponibles

### Base URL
```
http://localhost:8000/api/auth/
```

### Liste des endpoints

| Méthode | Endpoint | Description | Auth Requise |
|---------|----------|-------------|--------------|
| POST | `/register/` | Inscription avec email | Non |
| POST | `/login/` | Connexion email/username + password | Non |
| POST | `/token/` | Obtenir JWT tokens | Non |
| POST | `/token/refresh/` | Rafraîchir access token | Non |
| POST | `/logout/` | Déconnexion | Oui |
| GET | `/verify/` | Vérifier token JWT | Oui |
| POST | `/oauth/google/` | Connexion Google (V2) | Non |
| POST | `/oauth/apple/` | Connexion Apple (V2) | Non |

---

## 📧 Authentification Email + Password

### 1. Inscription

**Endpoint:** `POST /api/auth/register/`

**Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+221771234567"
}
```

**Réponse (201 Created):**
```json
{
  "message": "User registered successfully.",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "user",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 2. Connexion avec Email

**Endpoint:** `POST /api/auth/login/`

**Body (avec email):**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**OU avec username:**
```json
{
  "username": "john_doe",
  "password": "SecurePassword123!"
}
```

**Réponse (200 OK):**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "user",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "client",
    "is_verified": true
  }
}
```

### 3. Utilisation du Token

Ajoutez le token dans les headers de vos requêtes :

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### 4. Rafraîchir le Token

**Endpoint:** `POST /api/auth/token/refresh/`

**Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Réponse:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 5. Déconnexion

**Endpoint:** `POST /api/auth/logout/`

**Headers:**
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Réponse:**
```json
{
  "message": "Successfully logged out."
}
```

---

## 🌐 Google OAuth (V2)

### Prérequis
1. Créer un projet Google Cloud Console
2. Activer Google Sign-In API
3. Obtenir un Client ID
4. Configurer les URI de redirection

### Configuration

Ajoutez dans `settings/base.py` :
```python
# Google OAuth
GOOGLE_OAUTH_CLIENT_ID = 'votre-client-id.apps.googleusercontent.com'
```

### Intégration Frontend

**1. Installer Google Sign-In SDK**

Pour React Native (Expo) :
```bash
npx expo install @react-native-google-signin/google-signin
```

**2. Configurer Google Sign-In**

```typescript
import { GoogleSignin } from '@react-native-google-signin/google-signin';

GoogleSignin.configure({
  webClientId: 'VOTRE_WEB_CLIENT_ID.apps.googleusercontent.com',
  iosClientId: 'VOTRE_IOS_CLIENT_ID.apps.googleusercontent.com',
});
```

**3. Implémenter le bouton de connexion**

```typescript
const signInWithGoogle = async () => {
  try {
    await GoogleSignin.hasPlayServices();
    const userInfo = await GoogleSignin.signIn();
    
    // Envoyer le token à votre backend
    const response = await fetch('http://localhost:8000/api/auth/oauth/google/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id_token: userInfo.idToken,
      }),
    });
    
    const data = await response.json();
    // Sauvegarder les tokens JWT
    await AsyncStorage.setItem('access_token', data.access);
    await AsyncStorage.setItem('refresh_token', data.refresh);
    
  } catch (error) {
    console.error('Google Sign-In Error:', error);
  }
};
```

### Endpoint Backend

**Endpoint:** `POST /api/auth/oauth/google/`

**Body:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI..."
}
```

**Réponse (200 OK):**
```json
{
  "message": "Successfully authenticated with Google.",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john.doe",
    "email": "john.doe@gmail.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "client"
  }
}
```

---

## 🍎 Apple Sign In (V2)

### Prérequis
1. Compte Apple Developer
2. Activer Sign In with Apple
3. Configurer les identifiants

### Configuration

Ajoutez dans `settings/base.py` :
```python
# Apple Sign In
APPLE_CLIENT_ID = 'com.digithab.crm'
APPLE_TEAM_ID = 'VOTRE_TEAM_ID'
APPLE_KEY_ID = 'VOTRE_KEY_ID'
```

### Intégration Frontend

**1. Installer Apple Authentication**

Pour React Native (Expo) :
```bash
npx expo install expo-apple-authentication
```

**2. Configurer Apple Sign-In**

```typescript
import * as AppleAuthentication from 'expo-apple-authentication';

const signInWithApple = async () => {
  try {
    const credential = await AppleAuthentication.signInAsync({
      requestedScopes: [
        AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
        AppleAuthentication.AppleAuthenticationScope.EMAIL,
      ],
    });
    
    // Envoyer le token à votre backend
    const response = await fetch('http://localhost:8000/api/auth/oauth/apple/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id_token: credential.identityToken,
        user_data: {
          name: {
            firstName: credential.fullName?.givenName || '',
            lastName: credential.fullName?.familyName || '',
          },
        },
      }),
    });
    
    const data = await response.json();
    // Sauvegarder les tokens JWT
    await AsyncStorage.setItem('access_token', data.access);
    await AsyncStorage.setItem('refresh_token', data.refresh);
    
  } catch (error) {
    console.error('Apple Sign-In Error:', error);
  }
};
```

### Endpoint Backend

**Endpoint:** `POST /api/auth/oauth/apple/`

**Body:**
```json
{
  "id_token": "eyJraWQiOiJXNldjT0tC...",
  "user_data": {
    "name": {
      "firstName": "John",
      "lastName": "Doe"
    }
  }
}
```

**Réponse (200 OK):**
```json
{
  "message": "Successfully authenticated with Apple.",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john.doe",
    "email": "john.doe@privaterelay.appleid.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "client"
  }
}
```

---

## 📱 Exemples d'intégration

### React Native (Expo)

**1. Service d'authentification**

```typescript
// services/authService.ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/auth';

export const authService = {
  // Inscription
  async register(email: string, password: string, firstName: string, lastName: string) {
    const response = await axios.post(`${API_URL}/register/`, {
      email,
      password,
      password_confirm: password,
      first_name: firstName,
      last_name: lastName,
    });
    
    await this.saveTokens(response.data.access, response.data.refresh);
    return response.data;
  },

  // Connexion email + password
  async login(email: string, password: string) {
    const response = await axios.post(`${API_URL}/login/`, {
      email,
      password,
    });
    
    await this.saveTokens(response.data.access, response.data.refresh);
    return response.data;
  },

  // Connexion Google
  async loginWithGoogle(idToken: string) {
    const response = await axios.post(`${API_URL}/oauth/google/`, {
      id_token: idToken,
    });
    
    await this.saveTokens(response.data.access, response.data.refresh);
    return response.data;
  },

  // Connexion Apple
  async loginWithApple(idToken: string, userData: any) {
    const response = await axios.post(`${API_URL}/oauth/apple/`, {
      id_token: idToken,
      user_data: userData,
    });
    
    await this.saveTokens(response.data.access, response.data.refresh);
    return response.data;
  },

  // Déconnexion
  async logout() {
    const refreshToken = await AsyncStorage.getItem('refresh_token');
    const accessToken = await AsyncStorage.getItem('access_token');
    
    await axios.post(`${API_URL}/logout/`, 
      { refresh: refreshToken },
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    );
    
    await this.clearTokens();
  },

  // Sauvegarder tokens
  async saveTokens(access: string, refresh: string) {
    await AsyncStorage.setItem('access_token', access);
    await AsyncStorage.setItem('refresh_token', refresh);
  },

  // Supprimer tokens
  async clearTokens() {
    await AsyncStorage.removeItem('access_token');
    await AsyncStorage.removeItem('refresh_token');
  },

  // Obtenir access token
  async getAccessToken() {
    return await AsyncStorage.getItem('access_token');
  },
};
```

**2. Écran de connexion**

```typescript
// screens/LoginScreen.tsx
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity } from 'react-native';
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import * as AppleAuthentication from 'expo-apple-authentication';
import { authService } from '../services/authService';

export const LoginScreen = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleEmailLogin = async () => {
    try {
      const result = await authService.login(email, password);
      console.log('Login successful:', result);
      // Navigation vers l'écran principal
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      await GoogleSignin.hasPlayServices();
      const userInfo = await GoogleSignin.signIn();
      const result = await authService.loginWithGoogle(userInfo.idToken);
      console.log('Google login successful:', result);
    } catch (error) {
      console.error('Google login failed:', error);
    }
  };

  const handleAppleLogin = async () => {
    try {
      const credential = await AppleAuthentication.signInAsync({
        requestedScopes: [
          AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
          AppleAuthentication.AppleAuthenticationScope.EMAIL,
        ],
      });
      
      const result = await authService.loginWithApple(
        credential.identityToken!,
        {
          name: {
            firstName: credential.fullName?.givenName || '',
            lastName: credential.fullName?.familyName || '',
          },
        }
      );
      console.log('Apple login successful:', result);
    } catch (error) {
      console.error('Apple login failed:', error);
    }
  };

  return (
    <View>
      <TextInput
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
      />
      <TextInput
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <TouchableOpacity onPress={handleEmailLogin}>
        <Text>Se connecter</Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={handleGoogleLogin}>
        <Text>Continuer avec Google</Text>
      </TouchableOpacity>

      <AppleAuthentication.AppleAuthenticationButton
        buttonType={AppleAuthentication.AppleAuthenticationButtonType.SIGN_IN}
        buttonStyle={AppleAuthentication.AppleAuthenticationButtonStyle.BLACK}
        cornerRadius={5}
        style={{ width: 200, height: 44 }}
        onPress={handleAppleLogin}
      />
    </View>
  );
};
```

---

## 🔧 Installation des dépendances

### Backend (Django)

```bash
pip install google-auth
pip install PyJWT
pip install cryptography
```

### Frontend (React Native)

```bash
# Google Sign-In
npx expo install @react-native-google-signin/google-signin

# Apple Authentication
npx expo install expo-apple-authentication

# AsyncStorage pour les tokens
npx expo install @react-native-async-storage/async-storage

# Axios pour les requêtes API
npm install axios
```

---

## 📝 Notes importantes

1. **Tokens JWT** : Les tokens ont une durée de vie limitée (généralement 1h pour l'access token, 7 jours pour le refresh token)

2. **Sécurité** : 
   - Toujours utiliser HTTPS en production
   - Ne jamais exposer les Client IDs et secrets dans le code frontend
   - Stocker les tokens de manière sécurisée (Keychain iOS, Keystore Android)

3. **Test** : Utilisez Swagger UI pour tester les endpoints : `http://localhost:8000/api/docs/`

4. **OAuth V2** : Les endpoints Google et Apple OAuth nécessitent une configuration supplémentaire avec les providers respectifs.

---

## 🚀 Prochaines étapes

Pour compléter l'implémentation OAuth :

1. Configurer les projets sur Google Cloud Console et Apple Developer
2. Implémenter la vérification complète des tokens OAuth
3. Ajouter la gestion des erreurs OAuth
4. Tester l'intégration complète
5. Ajouter l'authentification par SMS/OTP (optionnel)

---

**Documentation mise à jour le:** 20 Novembre 2025
**Version:** 2.0.0

