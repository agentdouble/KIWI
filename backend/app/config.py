from pydantic_settings import BaseSettings
from typing import List, Literal, Optional, Union
from pydantic import Field
import os

class Settings(BaseSettings):
    # Mode de fonctionnement
    llm_mode: Literal["api", "local"] = Field(default="api", description="Mode API (provider externe OpenAI-compatible) ou Local (vLLM)")
    
    # Database
    db_name: str = "oskour"
    db_user: str = "GJV"
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5432
    database_url: str = ""
    
    # Security
    jwt_secret_key: str = Field(default=None)
    
    # Mistral API (pour fonctionnalités spécifiques: embeddings, Pixtral, MCP)
    mistral_api_key: str = Field(default=None)
    pixtral_model: str = "pixtral-large-latest"

    # API LLM (format OpenAI-compatible) pour le mode API
    api_url: str = Field(
        default="https://api.mistral.ai/v1/chat/completions",
        description="Endpoint /v1/chat/completions compatible OpenAI pour le LLM principal en mode API",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Clé API pour le fournisseur LLM principal (utilisée avec api_url)",
    )
    api_model: str = Field(
        default="mistral-small-latest",
        description="Identifiant du modèle utilisé sur l'API LLM principale (format OpenAI-compatible)",
    )
    
    # vLLM Configuration (pour mode local)
    vllm_api_url: str = "http://0.0.0.0:5263/v1/chat/completions"
    vllm_model_name: str = "Mistral-Small-3.1-24B-Instruct-2503"
    vllm_max_tokens: int = 6000
    vllm_temperature: float = 0.0
    vllm_timeout: int = 500  # secondes
    
    # Pixtral vLLM Configuration (pour mode local avec images)
    pixtral_vllm_url: str = "http://localhost:8085/v1/chat/completions"
    pixtral_vllm_model: str = "pixtral-large-latest"
    
    # App
    app_name: str = "FoyerGPT Backend"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False)
    
    # Backend Configuration
    server_host: str = Field(default="0.0.0.0", alias="backend_host")
    server_port: int = Field(default=8077, alias="backend_port")  # Default will be overridden by BACKEND_URL
    backend_url: str = Field(default="http://localhost:8077")
    
    # Frontend Configuration
    frontend_url: str = Field(default="http://localhost:8091")
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"
    
    # Session
    session_expire_hours: int = 24
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Storage
    storage_path: str = "./storage"
    max_file_size_mb: int = 10
    allowed_file_types: List[str] = Field(default_factory=lambda: [".pdf", ".docx", ".txt", ".md", ".doc", ".rtf", ".png", ".jpg", ".jpeg", ".gif", ".webp"])
    max_documents_per_agent: int = 10
    max_documents_per_chat: int = 5

    # Admins (identified by trigrammes)
    admin_trigrammes_raw: Optional[str] = Field(default=None, alias="ADMIN_TRIGRAMMES")
    
    # PDF Processing
    pdf_use_pixtral_threshold: int = 100  # Utiliser Pixtral si le texte extrait < 100 caractères
    pdf_max_pages_pixtral: int = 0  # 0 = pas de limite; sinon borne supérieure
    
    # Embeddings / RAG
    embedding_provider: str = "mistral"  # valeurs supportées: "mistral", "local"
    embedding_model: str = "mistral-embed"
    embedding_local_model_path: Optional[str] = None
    embedding_dimension: int = 1024
    embedding_chunk_size_chars: int = 1500
    embedding_chunk_overlap: int = 200
    embedding_batch_size: int = 64
    # RAG mode: n'injecte pas les docs bruts dans le system prompt
    rag_only: bool = True
    # pgvector
    pgvector_enabled: bool = True
    pgvector_ivfflat_lists: int = 100
    pgvector_ivfflat_probes: int = 10
    
    class Config:
        env_file = ".env"
        populate_by_name = True  # Permet d'utiliser les alias
        
    @property
    def sync_database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Extraire automatiquement le port depuis BACKEND_URL
        if self.backend_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(self.backend_url)
                if parsed.port:
                    self.server_port = parsed.port
                # Le host reste configurable via SERVER_HOST pour l'écoute
            except:
                pass
        
        # Les alias permettent d'utiliser backend_port et backend_host si nécessaire
        # mais on utilise server_port et server_host en interne
        
        if not self.database_url:
            self.database_url = f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        
        if not self.jwt_secret_key:
            self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
            if not self.jwt_secret_key:
                raise ValueError("JWT_SECRET_KEY environment variable is required")

        # Validation selon le mode
        if self.llm_mode == "api":
            # En mode API, le LLM principal utilise une API OpenAI-compatible
            if not self.api_url:
                raise ValueError("API_URL environment variable is required in API mode")

            if not self.api_key:
                # Permettre la configuration via variable d'environnement API_KEY
                self.api_key = os.getenv("API_KEY")

            if not self.api_key:
                raise ValueError("API_KEY environment variable is required in API mode")

        elif self.llm_mode == "local":
            # En mode local, vérifier que l'URL vLLM est configurée
            if not self.vllm_api_url:
                raise ValueError("vLLM_API_URL is required in local mode")
            if not self.pixtral_vllm_url:
                raise ValueError("PIXTRAL_VLLM_URL is required in local mode")
            # Log le mode pour confirmation
            print(f"🚀 Running in LOCAL mode with vLLM at {self.vllm_api_url}")

        # Synchroniser provider d'embeddings avec le mode LLM si explicite
        env_provider = os.getenv("EMBEDDING_PROVIDER")
        if env_provider is None:
            self.embedding_provider = "local" if self.llm_mode == "local" else "mistral"

        env_model = os.getenv("EMBEDDING_MODEL")
        if env_model is None and self.embedding_provider == "mistral":
            # Valeur par défaut cohérente pour Mistral
            self.embedding_model = "mistral-embed"

        if self.embedding_provider == "local":
            if not self.embedding_local_model_path:
                raise ValueError(
                    "EMBEDDING_LOCAL_MODEL_PATH is required when EMBEDDING_PROVIDER=local"
                )
        elif self.embedding_provider != "mistral":
            raise ValueError(
                "Unsupported EMBEDDING_PROVIDER. Use 'mistral' or 'local'."
            )
    
    @property
    def cors_origins_list(self) -> List[str]:
        def _normalize_origin(value: str) -> str:
            stripped = value.strip()
            while stripped.endswith('/') and '://' in stripped:
                stripped = stripped[:-1]
            return stripped

        origins = [_normalize_origin(origin) for origin in self.cors_origins.split(',') if origin.strip()]
        # Ajouter automatiquement les URLs frontend et backend configurées
        frontend = _normalize_origin(self.frontend_url) if self.frontend_url else None
        backend = _normalize_origin(self.backend_url) if self.backend_url else None

        if frontend and frontend not in origins:
            origins.append(frontend)
        if backend and backend not in origins:
            origins.append(backend)
        return origins
    
    @property
    def is_local_mode(self) -> bool:
        """Helper pour vérifier si on est en mode local"""
        return self.llm_mode == "local"
    
    @property
    def is_api_mode(self) -> bool:
        """Helper pour vérifier si on est en mode API"""
        return self.llm_mode == "api"

    def _normalize_admin_trigrammes(self, value: Optional[Union[str, List[str]]]) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            normalized: List[str] = []
            for item in value:
                if item is None:
                    continue
                text_item = str(item).strip().upper()
                if text_item:
                    normalized.append(text_item)
            return normalized
        if isinstance(value, str):
            if not value.strip():
                return []
            return [item.strip().upper() for item in value.split(',') if item.strip()]
        # Fallback: essayer de convertir tout autre type vers str
        text_value = str(value)
        if not text_value.strip():
            return []
        return [item.strip().upper() for item in text_value.split(',') if item.strip()]

    @property
    def admin_trigrammes(self) -> List[str]:
        if not hasattr(self, "_admin_trigrammes_cache"):
            self._admin_trigrammes_cache = self._normalize_admin_trigrammes(self.admin_trigrammes_raw)
        return self._admin_trigrammes_cache

settings = Settings()

# Log du mode au démarrage
print(f"🔧 Configuration loaded: LLM Mode = {settings.llm_mode}")
if settings.is_local_mode:
    print(f"   vLLM URL: {settings.vllm_api_url}")
    print(f"   Model: {settings.vllm_model_name}")
else:
    print(f"   API URL: {settings.api_url}")
    print(f"   API Model: {settings.api_model}")
