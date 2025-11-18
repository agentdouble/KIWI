# Démarrage Rapide - FoyerGPT

Ce guide vous permet de démarrer FoyerGPT en moins de 5 minutes.

## Prérequis

- Python 3.13+
- Node.js 18+
- PostgreSQL 14+

## Installation Express

### 1. Cloner et configurer

```bash
# Cloner le projet
git clone <repository-url>
cd foyergpt

# Configuration backend
cd backend
cp .env.example .env
# Éditer .env avec vos clés API
```

### 2. Base de données

```bash
# Créer la base
createdb oskour

# Dans le fichier backend/.env, configurer :
# DB_NAME=oskour
# DB_USER=votre_user
# DB_PASSWORD=votre_password
```

### 3. Installer et démarrer

**Terminal 1 - Backend :**
```bash
cd backend
pip install uv
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8061
```

**Terminal 2 - Frontend :**
```bash
cd frontend
npm install
npm run dev
```

## C'est prêt !

1. Ouvrez http://localhost:8060
2. Créez un compte
3. Commencez à chatter !

## Configuration Minimale (.env)

```env
# Backend .env minimal
DB_NAME=oskour
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432

SECRET_KEY=changez-moi-en-production
JWT_SECRET_KEY=changez-moi-aussi

# Ajoutez votre clé API
MISTRAL_API_KEY=votre-cle-mistral
```

## Commandes Utiles

```bash
# Backend
uv run pytest              # Tests
uv run alembic upgrade head  # Migrations

# Frontend  
npm run build             # Build production
npm run lint              # Vérifier le code
```

## Problèmes Fréquents

### Erreur de connexion PostgreSQL
```bash
# Vérifier que PostgreSQL est démarré
sudo systemctl status postgresql  # Linux
brew services list                 # macOS
```

### Port déjà utilisé
```bash
# Trouver et tuer le processus
lsof -i :8061  # ou :8060
kill -9 <PID>
```

### Erreur d'import Python
```bash
# Réinstaller les dépendances
cd backend
rm -rf .venv
uv venv
uv sync
```

## Prochaines Étapes

- [Guide d'utilisation](./docs/USAGE_GUIDE.md)
- [Architecture détaillée](./README.md)
- [Guide de développement](./docs/DEVELOPMENT.md)

---

**Astuce** : Utilisez `mistral-small` comme modèle par défaut pour des réponses plus rapides pendant le développement.