# Documentation API - FoyerGPT

## Vue d'ensemble

L'API FoyerGPT est une API RESTful construite avec FastAPI. Elle fournit des endpoints pour la gestion des utilisateurs, des agents IA, des conversations et des documents.

### URL de base

```
http://localhost:8061/api
```

### Format des réponses

Toutes les réponses sont au format JSON avec la structure suivante :

**Succès** :
```json
{
  "data": {},
  "status": "success"
}
```

**Erreur** :
```json
{
  "detail": "Message d'erreur",
  "status": "error"
}
```

### Authentification

L'API utilise l'authentification JWT Bearer. Incluez le token dans l'en-tête Authorization :

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### Authentification

#### POST /api/auth/register
Créer un nouveau compte utilisateur.

**Body** :
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "trigramme": "ABC"
}
```

**Réponse** :
```json
{
  "id": 1,
  "email": "user@example.com",
  "trigramme": "ABC",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Codes de statut** :
- `201` : Utilisateur créé avec succès
- `400` : Données invalides
- `409` : Email ou trigramme déjà existant

#### POST /api/auth/login
Se connecter et obtenir un token JWT.

**Body** :
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Réponse** :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "trigramme": "ABC"
  }
}
```

**Codes de statut** :
- `200` : Connexion réussie
- `401` : Identifiants invalides

#### POST /api/auth/logout
Se déconnecter (invalide le token côté serveur).

**Headers requis** :
- `Authorization: Bearer <token>`

**Réponse** :
```json
{
  "message": "Déconnexion réussie"
}
```

#### GET /api/auth/me
Obtenir les informations de l'utilisateur connecté.

**Headers requis** :
- `Authorization: Bearer <token>`

**Réponse** :
```json
{
  "id": 1,
  "email": "user@example.com",
  "trigramme": "ABC",
  "is_active": true,
  "is_admin": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Agents IA

#### GET /api/agents
Lister tous les agents publics.

**Query Parameters** :
- `limit` (optionnel) : Nombre d'agents à retourner (défaut: 20)
- `offset` (optionnel) : Pagination (défaut: 0)

**Réponse** :
```json
{
  "agents": [
    {
      "id": 1,
      "name": "Assistant Général",
      "system_prompt": "Tu es un assistant utile...",
      "learn_from_interaction": false,
      "is_public": true,
      "model": "mistral-small",
      "temperature": 0.7,
      "avatar_url": "/avatars/assistant.png",
      "owner": {
        "id": 1,
        "trigramme": "ABC"
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 10,
  "limit": 20,
  "offset": 0
}
```

#### GET /api/agents/my
Lister les agents de l'utilisateur connecté.

**Headers requis** :
- `Authorization: Bearer <token>`

**Réponse** :
```json
{
  "agents": [
    {
      "id": 2,
      "name": "Mon Assistant Privé",
      "system_prompt": "Tu es mon assistant personnel...",
      "learn_from_interaction": true,
      "is_public": false,
      "model": "mistral-medium",
      "temperature": 0.5,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /api/agents
Créer un nouvel agent.

**Headers requis** :
- `Authorization: Bearer <token>`

**Body** :
```json
{
  "name": "Expert Python",
  "system_prompt": "Tu es un expert en Python...",
  "learn_from_interaction": true,
  "is_public": false,
  "model": "mistral-medium",
  "temperature": 0.7,
  "avatar_url": "/avatars/python.png"
}
```

**Réponse** :
```json
{
  "id": 3,
  "name": "Expert Python",
  "system_prompt": "Tu es un expert en Python...",
  "learn_from_interaction": true,
  "is_public": false,
  "model": "mistral-medium",
  "temperature": 0.7,
  "avatar_url": "/avatars/python.png",
  "owner_id": 1,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Codes de statut** :
- `201` : Agent créé avec succès
- `400` : Données invalides
- `401` : Non authentifié

#### GET /api/agents/{agent_id}
Obtenir les détails d'un agent.

**Réponse** :
```json
{
  "id": 1,
  "name": "Assistant Général",
  "system_prompt": "Tu es un assistant utile...",
  "learn_from_interaction": false,
  "is_public": true,
  "model": "mistral-small",
  "temperature": 0.7,
  "avatar_url": "/avatars/assistant.png",
  "owner": {
    "id": 1,
    "trigramme": "ABC"
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### PUT /api/agents/{agent_id}
Modifier un agent (propriétaire uniquement).

**Headers requis** :
- `Authorization: Bearer <token>`

**Body** :
```json
{
  "name": "Expert Python Avancé",
  "temperature": 0.8
}
```

#### DELETE /api/agents/{agent_id}
Supprimer un agent (propriétaire uniquement).

**Headers requis** :
- `Authorization: Bearer <token>`

### Conversations (Chats)

#### GET /api/chats
Lister les conversations de l'utilisateur.

**Headers requis** :
- `Authorization: Bearer <token>`

**Query Parameters** :
- `limit` (optionnel) : Nombre de conversations (défaut: 20)
- `offset` (optionnel) : Pagination (défaut: 0)

**Réponse** :
```json
{
  "chats": [
    {
      "id": 1,
      "title": "Discussion Python",
      "agent": {
        "id": 3,
        "name": "Expert Python"
      },
      "last_message_at": "2024-01-01T10:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 5
}
```

#### POST /api/chats
Créer une nouvelle conversation.

**Headers requis** :
- `Authorization: Bearer <token>`

**Body** :
```json
{
  "agent_id": 3,
  "title": "Nouvelle discussion"  // optionnel
}
```

**Réponse** :
```json
{
  "id": 2,
  "title": "Nouvelle discussion",
  "user_id": 1,
  "agent_id": 3,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### GET /api/chats/{chat_id}
Obtenir une conversation avec ses messages.

**Headers requis** :
- `Authorization: Bearer <token>`

**Réponse** :
```json
{
  "id": 1,
  "title": "Discussion Python",
  "agent": {
    "id": 3,
    "name": "Expert Python",
    "avatar_url": "/avatars/python.png"
  },
  "messages": [
    {
      "id": 1,
      "content": "Comment créer une fonction en Python?",
      "role": "user",
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "content": "Pour créer une fonction en Python...",
      "role": "assistant",
      "llm_model": "mistral-medium",
      "created_at": "2024-01-01T00:01:00Z"
    }
  ],
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### PUT /api/chats/{chat_id}
Modifier le titre d'une conversation.

**Headers requis** :
- `Authorization: Bearer <token>`

**Body** :
```json
{
  "title": "Python - Fonctions avancées"
}
```

#### DELETE /api/chats/{chat_id}
Supprimer une conversation.

**Headers requis** :
- `Authorization: Bearer <token>`

### Messages

#### POST /api/messages
Envoyer un message dans une conversation.

**Headers requis** :
- `Authorization: Bearer <token>`

**Body** :
```json
{
  "chat_id": 1,
  "content": "Comment utiliser les décorateurs?",
  "files": []  // optionnel, IDs des documents attachés
}
```

**Réponse** :
```json
{
  "user_message": {
    "id": 3,
    "content": "Comment utiliser les décorateurs?",
    "role": "user",
    "chat_id": 1,
    "created_at": "2024-01-01T00:02:00Z"
  },
  "assistant_message": {
    "id": 4,
    "content": "Les décorateurs en Python sont...",
    "role": "assistant",
    "chat_id": 1,
    "llm_model": "mistral-medium",
    "created_at": "2024-01-01T00:02:01Z"
  }
}
```

#### GET /api/messages/stream/{chat_id}
Stream de messages en temps réel (Server-Sent Events).

**Headers requis** :
- `Authorization: Bearer <token>`

**Query Parameters** :
- `message` : Le message à envoyer

**Réponse** : Stream SSE
```
data: {"token": "Les", "message_id": 5}
data: {"token": " décorateurs", "message_id": 5}
data: {"token": " en", "message_id": 5}
data: [DONE]
```

### Documents

#### POST /api/documents/upload
Uploader un document.

**Headers requis** :
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Form Data** :
- `file` : Le fichier à uploader
- `entity_type` : Type d'entité ("agent" ou "chat")
- `entity_id` : ID de l'agent ou du chat

**Réponse** :
```json
{
  "id": 1,
  "filename": "guide_python.pdf",
  "file_size": 1048576,
  "mime_type": "application/pdf",
  "entity_type": "agent",
  "entity_id": 3,
  "uploaded_at": "2024-01-01T00:00:00Z"
}
```

**Codes de statut** :
- `201` : Document uploadé avec succès
- `400` : Type de fichier non supporté
- `413` : Fichier trop volumineux

#### GET /api/documents/{document_id}
Télécharger un document.

**Headers requis** :
- `Authorization: Bearer <token>`

**Réponse** : Le fichier binaire avec les headers appropriés

#### DELETE /api/documents/{document_id}
Supprimer un document.

**Headers requis** :
- `Authorization: Bearer <token>`

### Sessions

#### GET /api/sessions/current
Obtenir la session courante.

**Headers requis** :
- `Authorization: Bearer <token>`
- `X-Session-ID: <session-id>`

**Réponse** :
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "expires_at": "2024-01-08T00:00:00Z",
  "metadata": {
    "user_agent": "Mozilla/5.0...",
    "ip_address": "127.0.0.1"
  }
}
```

## WebSocket Events

### Connection

```javascript
const socket = io('http://localhost:8061', {
  path: '/ws/socket.io',
  auth: {
    token: 'your-jwt-token'
  }
});
```

### Events

#### join_chat
Rejoindre une conversation pour recevoir les mises à jour.

```javascript
socket.emit('join_chat', { chat_id: 1 });
```

#### leave_chat
Quitter une conversation.

```javascript
socket.emit('leave_chat', { chat_id: 1 });
```

#### typing
Envoyer un indicateur de frappe.

```javascript
socket.emit('typing', { 
  chat_id: 1, 
  is_typing: true 
});
```

#### user_typing (reçu)
Recevoir les indicateurs de frappe des autres utilisateurs.

```javascript
socket.on('user_typing', (data) => {
  console.log(`User ${data.user_id} is typing: ${data.is_typing}`);
});
```

#### new_message (reçu)
Recevoir les nouveaux messages en temps réel.

```javascript
socket.on('new_message', (message) => {
  console.log('New message:', message);
});
```

## Codes d'erreur

| Code | Description |
|------|-------------|
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Accès interdit |
| 404 | Ressource non trouvée |
| 409 | Conflit (ex: email déjà existant) |
| 413 | Payload trop large |
| 422 | Données non valides |
| 429 | Trop de requêtes |
| 500 | Erreur serveur |

## Limites et quotas

- **Rate limiting** : 60 requêtes par minute par IP
- **Upload de fichiers** : Max 10 MB par fichier
- **Types de fichiers** : PDF, DOCX, TXT, MD, PNG, JPG, JPEG
- **Messages** : Max 4000 caractères par message
- **Agents par utilisateur** : 50 agents maximum

## Exemples d'utilisation

### JavaScript/TypeScript

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8061/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Login
const login = async (email: string, password: string) => {
  const response = await api.post('/auth/login', { email, password });
  const { access_token } = response.data;
  
  // Stocker le token pour les requêtes futures
  api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
  
  return response.data;
};

// Créer un agent
const createAgent = async (agentData: any) => {
  const response = await api.post('/agents', agentData);
  return response.data;
};

// Envoyer un message
const sendMessage = async (chatId: number, content: string) => {
  const response = await api.post('/messages', {
    chat_id: chatId,
    content: content
  });
  return response.data;
};
```

### Python

```python
import requests

class FoyerGPTAPI:
    def __init__(self, base_url="http://localhost:8061/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
    
    def login(self, email, password):
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}"
        })
        return data
    
    def create_agent(self, name, system_prompt, **kwargs):
        response = self.session.post(
            f"{self.base_url}/agents",
            json={
                "name": name,
                "system_prompt": system_prompt,
                **kwargs
            }
        )
        response.raise_for_status()
        return response.json()
    
    def send_message(self, chat_id, content):
        response = self.session.post(
            f"{self.base_url}/messages",
            json={
                "chat_id": chat_id,
                "content": content
            }
        )
        response.raise_for_status()
        return response.json()

# Utilisation
api = FoyerGPTAPI()
api.login("user@example.com", "password")

# Créer un agent
agent = api.create_agent(
    name="Assistant Python",
    system_prompt="Tu es un expert Python",
    model="mistral-medium"
)

# Créer une conversation et envoyer un message
chat = api.session.post(f"{api.base_url}/chats", json={"agent_id": agent["id"]}).json()
response = api.send_message(chat["id"], "Comment optimiser ce code Python?")
```

### cURL

```bash
# Login
curl -X POST http://localhost:8061/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Créer un agent (remplacer TOKEN par votre token)
curl -X POST http://localhost:8061/api/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "name": "Assistant Bash",
    "system_prompt": "Tu es un expert en scripts Bash",
    "model": "mistral-small"
  }'

# Envoyer un message
curl -X POST http://localhost:8061/api/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "chat_id": 1,
    "content": "Comment créer un script de backup?"
  }'
```