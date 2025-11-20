# Architecture Backend - FoyerGPT

## Vue d'ensemble

Le backend de FoyerGPT est construit avec FastAPI, un framework Python moderne et performant. L'architecture suit les principes de séparation des responsabilités avec une structure en couches bien définie.

## Stack technologique

- **Framework** : FastAPI (Python 3.13+)
- **Base de données** : PostgreSQL avec SQLAlchemy 2.0 (async)
- **Cache** : Redis
- **Authentification** : JWT avec python-jose
- **Temps réel** : Socket.IO
- **LLM** : Mistral AI API / vLLM local
- **Gestion des dépendances** : UV

## Structure du projet

```
backend/
├── app/
│   ├── api/                    # Routes API
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentification
│   │   ├── agents.py          # Gestion des agents
│   │   ├── chats.py           # Conversations
│   │   ├── messages.py        # Messages
│   │   ├── documents.py       # Documents
│   │   └── sessions.py        # Sessions
│   │
│   ├── models/                 # Modèles de données
│   │   ├── __init__.py
│   │   ├── user.py            # Modèle utilisateur
│   │   ├── agent.py           # Modèle agent IA
│   │   ├── chat.py            # Modèle conversation
│   │   ├── message.py         # Modèle message
│   │   ├── document.py        # Modèle document
│   │   └── session.py         # Modèle session
│   │
│   ├── services/               # Logique métier
│   │   ├── __init__.py
│   │   ├── llm_service.py     # Service LLM
│   │   ├── chat_service.py    # Service chat
│   │   ├── agent_service.py   # Service agents
│   │   ├── document_service.py # Service documents
│   │   └── message_service.py # Service messages
│   │
│   ├── middleware/             # Middlewares
│   │   ├── __init__.py
│   │   ├── auth.py            # Middleware auth
│   │   └── logging.py         # Middleware logging
│   │
│   ├── config.py              # Configuration
│   ├── database.py            # Configuration DB
│   ├── dependencies.py        # Dépendances FastAPI
│   ├── exceptions.py          # Exceptions personnalisées
│   └── main.py                # Point d'entrée
│
├── alembic/                    # Migrations DB
├── tests/                      # Tests unitaires
├── uploads/                    # Stockage des fichiers
├── pyproject.toml              # Configuration projet
└── .env                        # Variables d'environnement
```

## Modèles de données

### User
```python
class User(Base):
    id: int
    email: str (unique)
    trigramme: str (unique, 3 lettres)
    hashed_password: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
```

### Agent
```python
class Agent(Base):
    id: int
    name: str
    system_prompt: str
    learn_from_interaction: bool
    is_public: bool
    owner_id: int (FK User)
    model: str
    temperature: float
    avatar_url: str
    created_at: datetime
    updated_at: datetime
```

### Chat
```python
class Chat(Base):
    id: int
    title: str
    user_id: int (FK User)
    agent_id: int (FK Agent)
    created_at: datetime
    updated_at: datetime
```

### Message
```python
class Message(Base):
    id: int
    content: str
    role: str (user/assistant/system)
    chat_id: int (FK Chat)
    llm_model: str
    llm_provider: str
    created_at: datetime
```

### Document
```python
class Document(Base):
    id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    entity_type: str (agent/chat)
    entity_id: int
    uploaded_at: datetime
```

## Services principaux

### LLMService

Le service LLM abstrait l'interaction avec les modèles d'IA :

```python
class LLMService:
    def __init__(self, mode: str = "mistral"):
        self.mode = mode
        self.client = self._initialize_client()
    
    async def generate_response(
        self,
        messages: List[Dict],
        model: str,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Union[str, AsyncGenerator]:
        # Logique de génération
```

**Modes supportés** :
- `mistral` : Utilise l'API Mistral AI
- `vllm` : Utilise un serveur vLLM local

### ChatService

Gère le cycle de vie des conversations :

```python
class ChatService:
    async def create_chat(user_id: int, agent_id: int) -> Chat
    async def get_user_chats(user_id: int) -> List[Chat]
    async def get_chat_with_messages(chat_id: int) -> Chat
    async def update_chat_title(chat_id: int, title: str) -> Chat
    async def delete_chat(chat_id: int) -> bool
```

### AgentService

Gère les agents IA :

```python
class AgentService:
    async def create_agent(data: AgentCreate, owner_id: int) -> Agent
    async def get_public_agents() -> List[Agent]
    async def get_user_agents(user_id: int) -> List[Agent]
    async def update_agent(agent_id: int, data: AgentUpdate) -> Agent
    async def delete_agent(agent_id: int) -> bool
```

### DocumentService

Traite l'upload et l'analyse de documents :

```python
class DocumentService:
    async def upload_document(file: UploadFile, entity_type: str, entity_id: int) -> Document
    async def extract_text(document: Document) -> str
    async def process_with_ocr(file_path: str) -> str
    async def delete_document(document_id: int) -> bool
```

## API Routes

### Authentication (`/api/auth`)

- `POST /register` - Inscription utilisateur
- `POST /login` - Connexion
- `POST /logout` - Déconnexion
- `GET /me` - Profil utilisateur actuel

### Agents (`/api/agents`)

- `GET /` - Liste des agents publics
- `GET /my` - Agents de l'utilisateur
- `POST /` - Créer un agent
- `GET /{agent_id}` - Détails d'un agent
- `PUT /{agent_id}` - Modifier un agent
- `DELETE /{agent_id}` - Supprimer un agent

### Chats (`/api/chats`)

- `GET /` - Liste des conversations
- `POST /` - Créer une conversation
- `GET /{chat_id}` - Détails d'une conversation
- `PUT /{chat_id}` - Modifier une conversation
- `DELETE /{chat_id}` - Supprimer une conversation

### Messages (`/api/messages`)

- `POST /` - Envoyer un message
- `GET /stream/{chat_id}` - Stream de messages
- `GET /chat/{chat_id}` - Messages d'une conversation

### Documents (`/api/documents`)

- `POST /upload` - Upload d'un document
- `GET /{document_id}` - Télécharger un document
- `DELETE /{document_id}` - Supprimer un document

## Sécurité

### Authentification JWT

```python
# Configuration JWT
JWT_SECRET_KEY = settings.jwt_secret_key
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DELTA = timedelta(days=7)

# Création d'un token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + JWT_EXPIRATION_DELTA
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
```

### Middleware d'authentification

```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user(user_id)
    if user is None:
        raise credentials_exception
    return user
```

## Configuration

### Variables d'environnement

```env
# Base de données
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-secret-key

# LLM
LLM_MODE=api

# Mode API
API_URL=https://api.mistral.ai/v1/chat/completions
API_KEY=your-api-key
API_MODEL=mistral-small-latest
PIXTRAL_MODEL=pixtral-large-latest

# Mode local vLLM
# Utilisez une URL joignable par le backend (localhost, IP interne, ...)
VLLM_API_URL=http://localhost:5263/v1/chat/completions
VLLM_MODEL_NAME=Mistral-Small-3.1-24B-Instruct-2503
PIXTRAL_VLLM_URL=http://localhost:8085/v1/chat/completions
PIXTRAL_VLLM_MODEL=pixtral-large-latest

# Embeddings
EMBEDDING_PROVIDER=mistral  # automatique si LLM_MODE=api
EMBEDDING_MODEL=mistral-embed
# EMBEDDING_LOCAL_MODEL_PATH=/home/llama/models/base_models/bge-reranker-large

# Application
APP_ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:8060"]
```

### Configuration par environnement

```python
class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Security
    jwt_secret_key: str
    
    # LLM
    llm_mode: str = "api"
    mistral_api_key: Optional[str]
    api_model: str = "mistral-small-latest"
    pixtral_model: str = "pixtral-large-latest"
    vllm_api_url: Optional[str]
    vllm_model_name: Optional[str]
    pixtral_vllm_url: Optional[str]
    pixtral_vllm_model: Optional[str]
    
    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
```

## WebSocket / Socket.IO

### Configuration Socket.IO

```python
# main.py
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*"
)

socket_app = socketio.ASGIApp(
    sio,
    socketio_path='/ws/socket.io'
)

app.mount("/ws", socket_app)
```

### Événements Socket.IO

```python
@sio.event
async def connect(sid, environ):
    await sio.emit('connected', {'sid': sid}, room=sid)

@sio.event
async def join_chat(sid, data):
    chat_id = data['chat_id']
    sio.enter_room(sid, f"chat_{chat_id}")
    
@sio.event
async def typing(sid, data):
    chat_id = data['chat_id']
    await sio.emit('user_typing', data, room=f"chat_{chat_id}", skip_sid=sid)
```

## Gestion des erreurs

### Exceptions personnalisées

```python
class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

class NotFoundError(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(404, detail)

class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(401, detail)
```

### Handler global

```python
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
```

## Performance et optimisations

### Connexions asynchrones

- Utilisation de `asyncpg` pour PostgreSQL
- `aioredis` pour Redis
- Requêtes HTTP asynchrones avec `httpx`

### Mise en cache

```python
# Cache Redis pour les résultats fréquents
async def get_cached_agents():
    cached = await redis.get("public_agents")
    if cached:
        return json.loads(cached)
    
    agents = await get_public_agents_from_db()
    await redis.setex("public_agents", 300, json.dumps(agents))
    return agents
```

### Rate limiting

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/messages")
@limiter.limit("10/minute")
async def create_message(request: Request, ...):
    # Logique
```

## Tests

### Structure des tests

```
tests/
├── conftest.py           # Fixtures pytest
├── test_auth.py          # Tests authentification
├── test_agents.py        # Tests agents
├── test_chats.py         # Tests conversations
└── test_messages.py      # Tests messages
```

### Exemple de test

```python
@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/agents",
        headers=auth_headers,
        json={
            "name": "Test Agent",
            "system_prompt": "You are a test agent"
        }
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Agent"
```

## Déploiement

### Production avec Uvicorn

```bash
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8061 \
    --workers 4 \
    --log-level info
```
