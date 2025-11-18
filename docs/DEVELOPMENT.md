# Guide de développement - FoyerGPT

Ce guide est destiné aux développeurs souhaitant contribuer au projet FoyerGPT ou l'étendre.

## Table des matières

1. [Configuration de l'environnement](#configuration-de-lenvironnement)
2. [Architecture et conventions](#architecture-et-conventions)
3. [Workflow de développement](#workflow-de-développement)
4. [Tests](#tests)
5. [Ajout de fonctionnalités](#ajout-de-fonctionnalités)
6. [Débogage](#débogage)
7. [Performance](#performance)
8. [Sécurité](#sécurité)

## Configuration de l'environnement

### Prérequis développeur

En plus des prérequis standards, installez :

- **Git** pour le versioning
- **VS Code** ou **PyCharm** (recommandés)
- **Postman** ou **Insomnia** pour tester l'API

### Configuration VS Code recommandée

**.vscode/settings.json** :
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "88"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

**Extensions recommandées** :
- Python
- Pylance
- Black Formatter
- ESLint
- Prettier
- Thunder Client (API testing)
- SQLite Viewer

### Configuration Git

```bash
# Configuration globale
git config --global user.name "Votre Nom"
git config --global user.email "votre.email@example.com"

# Hooks pre-commit (optionnel)
pip install pre-commit
pre-commit install
```

**.pre-commit-config.yaml** :
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.13

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88']

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0
    hooks:
      - id: prettier
        files: \.(js|jsx|ts|tsx|json|css|md)$
```

## Architecture et conventions

### Structure des branches

- `main` : Branche de production stable
- `develop` : Branche de développement
- `feature/*` : Nouvelles fonctionnalités
- `fix/*` : Corrections de bugs
- `refactor/*` : Refactoring du code

### Conventions de code

#### Python (Backend)

```python
# Imports groupés et ordonnés
import os
import sys
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.auth import AuthService


# Classes avec docstrings
class UserService:
    """Service pour la gestion des utilisateurs."""
    
    def __init__(self, db: Session):
        """
        Initialise le service utilisateur.
        
        Args:
            db: Session de base de données SQLAlchemy
        """
        self.db = db
        self.auth_service = AuthService()
    
    async def create_user(
        self, 
        email: str, 
        password: str, 
        trigramme: str
    ) -> User:
        """
        Crée un nouvel utilisateur.
        
        Args:
            email: Email de l'utilisateur
            password: Mot de passe en clair
            trigramme: Identifiant à 3 lettres
            
        Returns:
            User: L'utilisateur créé
            
        Raises:
            HTTPException: Si l'email existe déjà
        """
        # Vérifier l'unicité
        if await self.get_by_email(email):
            raise HTTPException(
                status_code=400,
                detail="Cet email est déjà utilisé"
            )
        
        # Créer l'utilisateur
        user = User(
            email=email,
            hashed_password=self.auth_service.hash_password(password),
            trigramme=trigramme.upper()
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user


# Constantes en majuscules
MAX_LOGIN_ATTEMPTS = 5
TOKEN_EXPIRY_HOURS = 24

# Fonctions avec type hints
def validate_email(email: str) -> bool:
    """Valide le format d'un email."""
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))
```

#### TypeScript/React (Frontend)

```typescript
// Interfaces pour les types
interface User {
  id: number;
  email: string;
  trigramme: string;
  createdAt: Date;
}

interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
}

// Composants fonctionnels avec types
interface UserCardProps {
  user: User;
  onEdit?: (user: User) => void;
  className?: string;
}

export const UserCard: React.FC<UserCardProps> = ({ 
  user, 
  onEdit, 
  className 
}) => {
  // Hooks en début de composant
  const [isEditing, setIsEditing] = useState(false);
  const { updateUser } = useUserStore();
  
  // Handlers avec useCallback pour la performance
  const handleEdit = useCallback(() => {
    if (onEdit) {
      onEdit(user);
    }
    setIsEditing(true);
  }, [user, onEdit]);
  
  // Early return pour les cas d'erreur
  if (!user) {
    return null;
  }
  
  // JSX avec formatage cohérent
  return (
    <Card className={cn("p-4", className)}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold">{user.trigramme}</h3>
          <p className="text-sm text-gray-600">{user.email}</p>
        </div>
        {onEdit && (
          <Button
            onClick={handleEdit}
            variant="outline"
            size="sm"
          >
            Éditer
          </Button>
        )}
      </div>
    </Card>
  );
};

// Custom hooks avec documentation
/**
 * Hook pour gérer l'authentification utilisateur
 * @returns {Object} État et méthodes d'authentification
 */
export const useAuth = () => {
  const { user, login, logout } = useAuthStore();
  const navigate = useNavigate();
  
  const handleLogin = async (credentials: LoginCredentials) => {
    try {
      await login(credentials);
      navigate('/dashboard');
    } catch (error) {
      toast.error('Échec de la connexion');
    }
  };
  
  return {
    user,
    isAuthenticated: !!user,
    login: handleLogin,
    logout
  };
};
```

### Conventions de nommage

- **Fichiers Python** : snake_case (`user_service.py`)
- **Fichiers TypeScript** : PascalCase pour composants (`UserCard.tsx`), camelCase pour autres (`useAuth.ts`)
- **Composants React** : PascalCase (`UserProfile`)
- **Variables/Fonctions** : camelCase en TS, snake_case en Python
- **Constantes** : UPPER_SNAKE_CASE
- **Interfaces TypeScript** : PascalCase sans préfixe I

## Workflow de développement

### 1. Créer une nouvelle fonctionnalité

```bash
# Créer une branche depuis develop
git checkout develop
git pull origin develop
git checkout -b feature/nom-de-la-feature

# Développer la fonctionnalité
# ... code ...

# Commits atomiques avec messages clairs
git add .
git commit -m "feat: ajouter la validation email au formulaire d'inscription"
git commit -m "test: ajouter tests unitaires pour la validation email"
git commit -m "docs: mettre à jour la documentation API"
```

### 2. Convention des messages de commit

Format : `<type>(<scope>): <subject>`

**Types** :
- `feat` : Nouvelle fonctionnalité
- `fix` : Correction de bug
- `docs` : Documentation
- `style` : Formatage (sans changement de code)
- `refactor` : Refactoring
- `perf` : Amélioration des performances
- `test` : Ajout de tests
- `chore` : Maintenance

**Exemples** :
```bash
feat(auth): ajouter l'authentification à double facteur
fix(chat): corriger le scroll automatique des messages
docs(api): documenter les endpoints de gestion des agents
refactor(frontend): migrer vers React Query v5
```

### 3. Pull Request

1. **Pousser la branche** :
```bash
git push origin feature/nom-de-la-feature
```

2. **Créer la PR sur GitHub** avec :
- Titre descriptif
- Description détaillée des changements
- Screenshots si changements UI
- Référence aux issues liées

3. **Template de PR** :
```markdown
## Description
Brève description des changements

## Type de changement
- [ ] Bug fix
- [ ] Nouvelle fonctionnalité
- [ ] Breaking change
- [ ] Documentation

## Tests
- [ ] Tests unitaires passent
- [ ] Tests d'intégration passent
- [ ] Tests manuels effectués

## Checklist
- [ ] Mon code suit les conventions du projet
- [ ] J'ai mis à jour la documentation
- [ ] J'ai ajouté des tests
- [ ] Tous les tests passent
```

## Tests

### Backend - Tests avec Pytest

#### Structure des tests
```
backend/tests/
├── conftest.py          # Fixtures globales
├── unit/                # Tests unitaires
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/         # Tests d'intégration
│   ├── test_api_auth.py
│   ├── test_api_agents.py
│   └── test_api_chats.py
└── e2e/                 # Tests end-to-end
    └── test_workflows.py
```

#### Exemple de test
```python
# tests/unit/test_services.py
import pytest
from unittest.mock import Mock, patch
from app.services.user_service import UserService
from app.exceptions import UserAlreadyExistsError

@pytest.fixture
def user_service():
    db_mock = Mock()
    return UserService(db_mock)

@pytest.fixture
def sample_user_data():
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "trigramme": "TST"
    }

class TestUserService:
    """Tests pour UserService."""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, sample_user_data):
        """Test la création réussie d'un utilisateur."""
        # Arrange
        user_service.get_by_email = Mock(return_value=None)
        
        # Act
        user = await user_service.create_user(**sample_user_data)
        
        # Assert
        assert user.email == sample_user_data["email"]
        assert user.trigramme == "TST"
        assert user.hashed_password != sample_user_data["password"]
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service, sample_user_data):
        """Test l'erreur lors d'un email dupliqué."""
        # Arrange
        existing_user = Mock()
        user_service.get_by_email = Mock(return_value=existing_user)
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsError):
            await user_service.create_user(**sample_user_data)

# Exécution des tests
# pytest tests/unit/test_services.py -v
# pytest --cov=app tests/  # Avec couverture
```

### Frontend - Tests avec Jest et React Testing Library

#### Configuration Jest
```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
  ],
};
```

#### Exemple de test composant
```typescript
// src/components/UserCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { UserCard } from './UserCard';

const mockUser = {
  id: 1,
  email: 'test@example.com',
  trigramme: 'TST',
  createdAt: new Date('2024-01-01')
};

describe('UserCard', () => {
  it('renders user information correctly', () => {
    render(<UserCard user={mockUser} />);
    
    expect(screen.getByText('TST')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });
  
  it('calls onEdit when edit button is clicked', () => {
    const handleEdit = jest.fn();
    render(<UserCard user={mockUser} onEdit={handleEdit} />);
    
    const editButton = screen.getByText('Éditer');
    fireEvent.click(editButton);
    
    expect(handleEdit).toHaveBeenCalledWith(mockUser);
  });
  
  it('does not render edit button when onEdit is not provided', () => {
    render(<UserCard user={mockUser} />);
    
    expect(screen.queryByText('Éditer')).not.toBeInTheDocument();
  });
});
```

## Ajout de fonctionnalités

### Exemple : Ajouter un système de favoris

#### 1. Backend - Modèle de données

```python
# app/models/favorite.py
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.database import Base

class Favorite(Base):
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'agent_id', name='_user_agent_uc'),
    )
```

#### 2. Backend - Migration

```bash
alembic revision --autogenerate -m "Add favorites table"
alembic upgrade head
```

#### 3. Backend - Service

```python
# app/services/favorite_service.py
class FavoriteService:
    def __init__(self, db: Session):
        self.db = db
    
    async def toggle_favorite(self, user_id: int, agent_id: int) -> bool:
        """Toggle favorite status for an agent."""
        favorite = self.db.query(Favorite).filter(
            Favorite.user_id == user_id,
            Favorite.agent_id == agent_id
        ).first()
        
        if favorite:
            self.db.delete(favorite)
            is_favorite = False
        else:
            self.db.add(Favorite(user_id=user_id, agent_id=agent_id))
            is_favorite = True
        
        await self.db.commit()
        return is_favorite
```

#### 4. Backend - API Endpoint

```python
# app/api/favorites.py
@router.post("/toggle/{agent_id}")
async def toggle_favorite(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = FavoriteService(db)
    is_favorite = await service.toggle_favorite(current_user.id, agent_id)
    return {"is_favorite": is_favorite}
```

#### 5. Frontend - API Service

```typescript
// src/lib/api/services/favoriteService.ts
export const favoriteApi = {
  toggle: async (agentId: number): Promise<{ isFavorite: boolean }> => {
    const response = await apiClient.post(`/favorites/toggle/${agentId}`);
    return response.data;
  }
};
```

#### 6. Frontend - Hook

```typescript
// src/hooks/useFavorites.ts
export const useFavorites = () => {
  const queryClient = useQueryClient();
  
  const toggleMutation = useMutation({
    mutationFn: favoriteApi.toggle,
    onMutate: async (agentId) => {
      // Optimistic update
      await queryClient.cancelQueries(['agent', agentId]);
      const previousAgent = queryClient.getQueryData(['agent', agentId]);
      
      queryClient.setQueryData(['agent', agentId], (old: any) => ({
        ...old,
        isFavorite: !old.isFavorite
      }));
      
      return { previousAgent };
    },
    onError: (err, agentId, context) => {
      // Rollback on error
      queryClient.setQueryData(['agent', agentId], context.previousAgent);
    },
    onSettled: (data, error, agentId) => {
      queryClient.invalidateQueries(['agent', agentId]);
    }
  });
  
  return {
    toggleFavorite: toggleMutation.mutate
  };
};
```

#### 7. Frontend - Composant

```typescript
// src/components/FavoriteButton.tsx
interface FavoriteButtonProps {
  agentId: number;
  isFavorite: boolean;
}

export const FavoriteButton: React.FC<FavoriteButtonProps> = ({ 
  agentId, 
  isFavorite 
}) => {
  const { toggleFavorite } = useFavorites();
  
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => toggleFavorite(agentId)}
      className={cn(isFavorite && "text-yellow-500")}
    >
      <Star className={cn("h-4 w-4", isFavorite && "fill-current")} />
    </Button>
  );
};
```

## Débogage

### Backend - Techniques de débogage

#### 1. Logging structuré

```python
# app/utils/logger.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        handler.setFormatter(self.JsonFormatter())
        self.logger.addHandler(handler)
    
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            if hasattr(record, 'extra_data'):
                log_data.update(record.extra_data)
            return json.dumps(log_data)
    
    def info(self, message, **kwargs):
        self.logger.info(message, extra={'extra_data': kwargs})

# Utilisation
logger = StructuredLogger(__name__)
logger.info("User login attempt", user_id=user.id, ip=request.client.host)
```

#### 2. Debugger Python

```python
# Utiliser debugpy pour VS Code
import debugpy

# Activer le débogage distant
debugpy.listen(5678)
debugpy.wait_for_client()  # Pause jusqu'à connexion du debugger

# Ou utiliser breakpoint() pour pdb
def complex_function(data):
    processed = preprocess(data)
    breakpoint()  # Arrêt ici pour inspection
    result = calculate(processed)
    return result
```

### Frontend - Outils de débogage

#### 1. React DevTools

```typescript
// Ajouter des labels pour faciliter le débogage
UserCard.displayName = 'UserCard';

// Utiliser les React DevTools Profiler
<Profiler id="UserList" onRender={onRenderCallback}>
  <UserList users={users} />
</Profiler>
```

#### 2. Console logging amélioré

```typescript
// src/utils/debug.ts
export const debug = {
  log: (message: string, data?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`🔍 ${message}`, data);
    }
  },
  error: (message: string, error: any) => {
    console.error(`❌ ${message}`, error);
  },
  api: (method: string, url: string, data?: any) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`🌐 ${method} ${url}`, data);
    }
  }
};

// Utilisation
debug.log('User state updated', { user });
debug.api('POST', '/api/auth/login', { email });
```

## Performance

### Backend - Optimisations

#### 1. Requêtes de base de données

```python
# ❌ N+1 queries
users = db.query(User).all()
for user in users:
    print(user.agents)  # Requête pour chaque user

# ✅ Eager loading
users = db.query(User).options(
    joinedload(User.agents)
).all()

# ✅ Sélection de colonnes spécifiques
users = db.query(User.id, User.email).all()

# ✅ Pagination
def get_paginated_users(page: int = 1, per_page: int = 20):
    return db.query(User)\
        .offset((page - 1) * per_page)\
        .limit(per_page)\
        .all()
```

#### 2. Mise en cache

```python
# app/utils/cache.py
from functools import lru_cache
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cache_key_wrapper(prefix: str, ttl: int = 300):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Générer la clé de cache
            cache_key = f"{prefix}:{':'.join(map(str, args))}"
            
            # Vérifier le cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Calculer et mettre en cache
            result = await func(*args, **kwargs)
            redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(result, default=str)
            )
            return result
        return wrapper
    return decorator

# Utilisation
@cache_key_wrapper("agents:public", ttl=600)
async def get_public_agents():
    return db.query(Agent).filter(Agent.is_public == True).all()
```

### Frontend - Optimisations

#### 1. Code splitting

```typescript
// Routes avec lazy loading
const Marketplace = lazy(() => import('./pages/Marketplace'));
const AgentDetails = lazy(() => import('./pages/AgentDetails'));

// Component splitting
const HeavyComponent = lazy(() => 
  import('./components/HeavyComponent')
);

// Utilisation
<Suspense fallback={<LoadingSpinner />}>
  <HeavyComponent />
</Suspense>
```

#### 2. Memoization

```typescript
// Composant mémorisé
const ExpensiveList = memo(({ items }: { items: Item[] }) => {
  return (
    <ul>
      {items.map(item => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  );
}, (prevProps, nextProps) => {
  // Comparaison personnalisée
  return prevProps.items.length === nextProps.items.length;
});

// Hook mémorisé
const useFilteredItems = (items: Item[], filter: string) => {
  return useMemo(() => {
    return items.filter(item => 
      item.name.toLowerCase().includes(filter.toLowerCase())
    );
  }, [items, filter]);
};
```

#### 3. Virtualisation

```typescript
// Pour les longues listes
import { FixedSizeList } from 'react-window';

const VirtualizedMessages = ({ messages }: { messages: Message[] }) => {
  const Row = ({ index, style }: { index: number; style: any }) => (
    <div style={style}>
      <Message message={messages[index]} />
    </div>
  );
  
  return (
    <FixedSizeList
      height={600}
      itemCount={messages.length}
      itemSize={80}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
};
```

## Sécurité

### Bonnes pratiques de sécurité

#### 1. Validation des entrées

```python
# Backend - Pydantic pour la validation
from pydantic import BaseModel, EmailStr, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    trigramme: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Le mot de passe doit faire au moins 8 caractères')
        if not any(c.isupper() for c in v):
            raise ValueError('Le mot de passe doit contenir une majuscule')
        if not any(c.isdigit() for c in v):
            raise ValueError('Le mot de passe doit contenir un chiffre')
        return v
    
    @validator('trigramme')
    def validate_trigramme(cls, v):
        if len(v) != 3 or not v.isalpha():
            raise ValueError('Le trigramme doit être composé de 3 lettres')
        return v.upper()
```

#### 2. Protection CSRF

```typescript
// Frontend - Inclure le token CSRF
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

apiClient.defaults.headers.common['X-CSRF-Token'] = csrfToken;
```

#### 3. Sanitisation des données

```typescript
// Frontend - Éviter les XSS
import DOMPurify from 'dompurify';

const SafeHtml = ({ html }: { html: string }) => {
  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
    ALLOWED_ATTR: ['href', 'target']
  });
  
  return <div dangerouslySetInnerHTML={{ __html: clean }} />;
};
```

#### 4. Rate limiting

```python
# Backend - Protection contre le brute force
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginCredentials):
    # Logique de connexion
    pass
```

### Gestion des secrets

```python
# Ne jamais commiter de secrets
# Utiliser des variables d'environnement

# .env.example (commité)
DATABASE_URL=postgresql://user:password@localhost/dbname
JWT_SECRET_KEY=your-secret-key-here
MISTRAL_API_KEY=your-api-key-here

# .env (ignoré par git)
DATABASE_URL=postgresql://prod_user:$3cur3P@ss@db.server/proddb
JWT_SECRET_KEY=d8f7a9s8d7f98a7sdf987asdf987asdf
MISTRAL_API_KEY=msk_a8s7df6a8s7df687asdf687asdf

# Validation au démarrage
if not settings.jwt_secret_key or settings.jwt_secret_key == "your-secret-key-here":
    raise ValueError("JWT_SECRET_KEY must be set in production")
```

## Monitoring et logs

### Structure de logging

```python
# app/utils/monitoring.py
import time
from functools import wraps
from prometheus_client import Counter, Histogram, generate_latest

# Métriques Prometheus
request_count = Counter(
    'app_requests_total', 
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'app_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

def track_request(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            status = 'success'
            return result
        except Exception as e:
            status = 'error'
            raise
        finally:
            duration = time.time() - start
            endpoint = kwargs.get('request').url.path
            method = kwargs.get('request').method
            
            request_count.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    return wrapper

# Endpoint pour les métriques
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Ressources supplémentaires

### Documentation officielle
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [TypeScript](https://www.typescriptlang.org/docs/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)

### Outils recommandés
- [Postman](https://www.postman.com/) - Tests API
- [React DevTools](https://react.dev/learn/react-developer-tools)
- [Redux DevTools](https://github.com/reduxjs/redux-devtools)
- [Python Debugger](https://docs.python.org/3/library/pdb.html)

### Communauté
- Discord du projet (lien à ajouter)
- Forum de discussion
- Issues GitHub

## Conclusion

Ce guide couvre les aspects essentiels du développement sur FoyerGPT. Pour toute question non couverte, n'hésitez pas à :
- Consulter le code existant pour des exemples
- Demander sur le Discord
- Ouvrir une issue GitHub

Bon développement !