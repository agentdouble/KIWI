# Guide d'installation - FoyerGPT

Ce guide détaille l'installation complète de FoyerGPT sur votre environnement local.

## Prérequis système

### Logiciels requis

- **Python** 3.13 ou supérieur
- **Node.js** 18.0 ou supérieur
- **PostgreSQL** 14.0 ou supérieur
- **Redis** 6.0 ou supérieur (optionnel, pour le cache)
- **Git** pour cloner le repository

### Ressources système recommandées

- **CPU** : 2 cores minimum
- **RAM** : 4 GB minimum (8 GB recommandé)
- **Stockage** : 2 GB d'espace libre

## Installation étape par étape

### 1. Cloner le repository

```bash
git clone <repository-url>
cd foyergpt
```

### 2. Configuration de la base de données

#### Installation de PostgreSQL

**macOS (avec Homebrew)** :
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Ubuntu/Debian** :
```bash
sudo apt update
sudo apt install postgresql-14 postgresql-client-14
sudo systemctl start postgresql
```

**Windows** :
Télécharger et installer depuis [postgresql.org](https://www.postgresql.org/download/windows/)

#### Création de la base de données

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer un utilisateur (remplacer 'password' par votre mot de passe)
CREATE USER foyergpt_user WITH PASSWORD 'password';

# Créer la base de données
CREATE DATABASE oskour OWNER foyergpt_user;

# Donner tous les privilèges
GRANT ALL PRIVILEGES ON DATABASE oskour TO foyergpt_user;

# Sortir
\q
```

### 3. Configuration de Redis (optionnel)

**macOS** :
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian** :
```bash
sudo apt install redis-server
sudo systemctl start redis-server
```

### 4. Installation du backend

#### Naviguer vers le dossier backend

```bash
cd backend
```

#### Installation avec UV (recommandé)

```bash
# Installer UV si nécessaire
pip install uv

# Créer l'environnement virtuel et installer les dépendances
uv venv
uv sync
```

#### Configuration de l'environnement

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer le fichier .env
nano .env  # ou votre éditeur préféré
```

Contenu du fichier `.env` :

```env
# Base de données
DATABASE_URL=postgresql+asyncpg://foyergpt_user:password@localhost:5432/oskour
DB_NAME=oskour
DB_USER=foyergpt_user
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Redis (optionnel)
REDIS_URL=redis://localhost:6379

# Sécurité
SECRET_KEY=your-very-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production

# Mode LLM (api ou local)
LLM_MODE=api

# API IA (si mode api)
MISTRAL_API_KEY=your-mistral-api-key
MISTRAL_MODEL=mistral-small-latest
VISION_MODEL=pixtral-large-latest
# Optionnel : endpoint custom compatible OpenAI pour un VLM tiers
# VISION_API_URL=https://api.mistral.ai/v1/chat/completions
# VISION_API_KEY=${MISTRAL_API_KEY}

# vLLM (si mode local)
# Utilisez une URL joignable par le backend (localhost, IP interne, ...)
VLLM_API_URL=http://localhost:5263/v1/chat/completions
VLLM_MODEL_NAME=Mistral-Small-3.1-24B-Instruct-2503
VISION_VLLM_URL=http://localhost:8085/v1/chat/completions
VISION_VLLM_MODEL=pixtral-large-latest

# Embeddings
EMBEDDING_PROVIDER=mistral  # automatique si LLM_MODE=api
EMBEDDING_MODEL=mistral-embed
# EMBEDDING_LOCAL_MODEL_PATH=/home/llama/models/base_models/bge-reranker-large

# Application
APP_ENV=development
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=["http://localhost:8060"]
```

#### Migrations de base de données

```bash
# Activer l'environnement virtuel
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Exécuter les migrations
alembic upgrade head
```

### 5. Installation du frontend

#### Naviguer vers le dossier frontend

```bash
cd ../frontend
```

#### Installation des dépendances

```bash
# Avec npm
npm install

# Ou avec yarn
yarn install

# Ou avec pnpm
pnpm install
```

#### Configuration de l'environnement

```bash
# Copier le fichier d'exemple si nécessaire
cp .env.example .env
```

Contenu du fichier `.env` (généralement pas nécessaire, les valeurs par défaut fonctionnent) :

```env
VITE_API_URL=http://localhost:8061/api
VITE_WS_URL=http://localhost:8061
```

### 6. Démarrage de l'application

#### Terminal 1 - Backend

```bash
cd backend
source .venv/bin/activate  # Activer l'environnement virtuel
uvicorn app.main:app --reload --port 8061
```

Le backend sera accessible sur `http://localhost:8061`

#### Terminal 2 - Frontend

```bash
cd frontend
npm run dev
```

Le frontend sera accessible sur `http://localhost:8060`

## Configuration avancée

### Configuration pour production

#### Backend

1. **Variables d'environnement de production** :
```env
APP_ENV=production
LOG_LEVEL=WARNING
SECRET_KEY=<clé-secrète-forte>
JWT_SECRET_KEY=<clé-jwt-forte>
```

2. **Démarrage avec Gunicorn** :
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8061
```

#### Frontend

1. **Build de production** :
```bash
npm run build
```

2. **Servir avec un serveur web** :
```bash
# Avec serve
npx serve -s dist -l 8060

# Ou avec nginx (voir configuration ci-dessous)
```

### Configuration Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /var/www/foyergpt/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API Backend
    location /api {
        proxy_pass http://localhost:8061;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8061;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```


## Vérification de l'installation

### 1. Vérifier le backend

```bash
# Tester l'API
curl http://localhost:8061/api/health

# Réponse attendue
{"status": "healthy", "timestamp": "2024-01-01T00:00:00"}
```

### 2. Vérifier le frontend

Ouvrir `http://localhost:8060` dans votre navigateur. Vous devriez voir la page de connexion.

### 3. Créer un compte test

1. Cliquer sur "S'inscrire"
2. Remplir le formulaire avec :
   - Email valide
   - Mot de passe (min 8 caractères)
   - Trigramme (3 lettres, ex: ABC)
3. Se connecter avec les identifiants créés

## Résolution des problèmes courants

### Erreur de connexion à PostgreSQL

```bash
# Vérifier que PostgreSQL est démarré
sudo systemctl status postgresql

# Vérifier les logs
sudo journalctl -u postgresql
```

### Erreur de dépendances Python

```bash
# Réinstaller avec UV
uv sync --refresh

# Ou nettoyer et réinstaller
rm -rf .venv
uv venv
uv sync
```

### Erreur de build frontend

```bash
# Nettoyer le cache
rm -rf node_modules package-lock.json
npm install

# Vérifier la version de Node
node --version  # Doit être >= 18
```

### Port déjà utilisé

```bash
# Trouver le processus utilisant le port
lsof -i :8061  # Backend
lsof -i :8060  # Frontend

# Tuer le processus
kill -9 <PID>
```

## Support

Pour obtenir de l'aide :

1. Consulter la [documentation complète](./README.md)
2. Vérifier les logs d'erreur
3. Ouvrir une issue sur le repository

## Prochaines étapes

Une fois l'installation terminée :

1. [Créer votre premier agent IA](./USAGE_GUIDE.md)
2. [Explorer l'API](./API_DOCUMENTATION.md)
3. [Contribuer au projet](./CONTRIBUTING.md)
