# FoyerGPT - Plateforme de Chat IA Multi-Agents

FoyerGPT est une plateforme moderne de chat IA qui permet aux utilisateurs de créer et d'interagir avec des agents IA personnalisés. L'application offre une expérience utilisateur fluide avec des capacités temps réel et un support pour l'intégration de documents.

## Fonctionnalités principales

### Gestion des utilisateurs
- Système d'authentification sécurisé avec JWT
- Inscription avec email et trigramme unique (identifiant à 3 lettres)
- Gestion des sessions avec expiration automatique
- Avatar utilisateur personnalisable

### Agents IA personnalisables
- Création d'agents IA avec des prompts système personnalisés
- Configuration des capacités d'apprentissage
- Support multimodal (texte et documents)
- Marketplace d'agents publics
- Gestion des agents privés par utilisateur

### Interface de chat avancée
- Conversations en temps réel avec streaming des réponses
- Support des fichiers et documents (PDF, DOCX, images, etc.)
- Historique des conversations persistant
- Export des conversations
- Indicateurs de frappe en temps réel

### Traitement intelligent de documents
- Upload et analyse de documents multiformats
- Extraction de texte avec OCR pour les images
- Intégration contextuelle dans les conversations
- Support pour PDF, DOCX, TXT, MD, et images

### Modes LLM flexibles
- **Mode API** : Intégration avec l'API Mistral
- **Mode Local** : Support vLLM pour l'inférence locale
- Configuration dynamique selon les besoins

## Architecture technique

### Backend (Python/FastAPI)
- **Framework** : FastAPI avec support async/await complet
- **Base de données** : PostgreSQL avec SQLAlchemy 2.0
- **Cache** : Redis pour les performances
- **Temps réel** : Socket.IO pour les WebSockets
- **Sécurité** : JWT, bcrypt, rate limiting

### Frontend (React/TypeScript)
- **Framework** : React 19 avec TypeScript
- **Build** : Vite pour un développement rapide
- **État** : Zustand + React Query
- **UI** : Tailwind CSS + Radix UI
- **Routing** : React Router v7

## Structure du projet

```
.
├── backend/                    # Application backend FastAPI
│   ├── app/
│   │   ├── api/               # Routes API REST
│   │   ├── models/            # Modèles SQLAlchemy
│   │   ├── services/          # Logique métier
│   │   ├── config.py          # Configuration
│   │   └── main.py            # Point d'entrée
│   ├── alembic/               # Migrations de base de données
│   └── tests/                 # Tests unitaires
│
├── frontend/                   # Application frontend React
│   ├── src/
│   │   ├── components/        # Composants React
│   │   ├── pages/            # Pages de l'application
│   │   ├── hooks/            # React hooks personnalisés
│   │   ├── stores/           # État global (Zustand)
│   │   ├── lib/              # Utilitaires et API
│   │   └── App.tsx           # Composant racine
│   └── public/               # Assets statiques
│
└── docs/                      # Documentation du projet
```

## Démarrage Rapide

Pour une installation rapide, consultez le [Guide de Démarrage Rapide](./QUICK_START.md).

### Prérequis
- Python 3.13+
- Node.js 18+
- PostgreSQL 14+
- Redis (optionnel, pour le cache)

### Installation Complète

Pour une installation détaillée, consultez le [Guide d'Installation](./docs/INSTALLATION.md).

**En résumé :**
```bash
# 1. Cloner et configurer
git clone <repository-url>
cd foyergpt
cd backend && cp .env.example .env
cd ../frontend && cp .env.example .env

# 2. Base de données
createdb oskour

# 3. Backend (Terminal 1)
cd backend
pip install uv
uv sync
uv run alembic upgrade head
uv run python run.py

# 4. Frontend (Terminal 2)
cd frontend
npm install
npm run dev

# 5. Ouvrir http://localhost:8091
```

### Lancement simplifié avec `start.sh`

Pour démarrer plus rapidement, vous pouvez utiliser le script de démarrage à la racine :

```bash
./start.sh
```

Ce script :
- libère les ports nécessaires,
- vérifie votre version de Node.js,
- exécute automatiquement `npm install` dans `frontend`,
- lance le backend (via `uv run python run.py`) et le frontend (`npm run dev`).

## Documentation

### Pour commencer
- [**Démarrage Rapide**](./QUICK_START.md) - Lancez FoyerGPT en 5 minutes
- [**Guide d'utilisation**](./docs/USAGE_GUIDE.md) - Apprenez à utiliser FoyerGPT

### Documentation technique
- [Architecture Backend](./docs/BACKEND_ARCHITECTURE.md) - Structure et conception du backend
- [Architecture Frontend](./docs/FRONTEND_ARCHITECTURE.md) - Structure et conception du frontend
- [Guide d'installation complet](./docs/INSTALLATION.md) - Installation détaillée et configuration
- [Documentation API](./docs/API_DOCUMENTATION.md) - Référence complète de l'API REST
- [Guide de développement](./docs/DEVELOPMENT.md) - Pour contribuer au projet

## Configuration

### Variables d'environnement Backend

```env
# Base de données
DB_NAME=oskour
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Sécurité
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Mode LLM (api ou local)
LLM_MODE=api

# Mode API (Mistral Cloud)
MISTRAL_API_KEY=your-mistral-key
MISTRAL_MODEL=mistral-small-latest
PIXTRAL_MODEL=pixtral-large-latest

# Mode local (vLLM + Pixtral)
# Utilisez une URL joignable depuis le backend (localhost, IP privée, ...)
VLLM_API_URL=http://localhost:5263/v1/chat/completions
VLLM_MODEL_NAME=Mistral-Small-3.1-24B-Instruct-2503
PIXTRAL_VLLM_URL=http://localhost:8085/v1/chat/completions
PIXTRAL_VLLM_MODEL=pixtral-large-latest

# Embeddings
EMBEDDING_PROVIDER=mistral  # automatique si LLM_MODE=api
EMBEDDING_MODEL=mistral-embed
# EMBEDDING_LOCAL_MODEL_PATH=/home/llama/models/base_models/bge-reranker-large (obligatoire si EMBEDDING_PROVIDER=local)
```

### Configuration Frontend

Le frontend se connecte automatiquement au backend via la variable d'environnement `VITE_BACKEND_URL` (par défaut `http://localhost:8077` dans `frontend/.env.example`), et est servi sur `VITE_FRONTEND_URL` (par défaut `http://localhost:8091`).

## Tests

```bash
# Tests backend
cd backend
uv run pytest

# Tests frontend
cd frontend
npm test
```

## Contribution

Les contributions sont les bienvenues ! Veuillez suivre ces étapes :

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence propriétaire. Tous droits réservés.

## Remerciements

- FastAPI pour le framework backend performant
- React pour l'interface utilisateur moderne
- Mistral AI pour les capacités d'intelligence artificielle
- La communauté open source pour les nombreuses bibliothèques utilisées
