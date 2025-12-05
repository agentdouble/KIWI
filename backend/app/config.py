from pydantic_settings import BaseSettings
from typing import List, Literal, Optional, Union
from pydantic import Field, AliasChoices
import logging
import os


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Mode de fonctionnement
    llm_mode: Literal["api", "local"] = Field(default="api", description="Mode API (OpenAI standard) ou Local (vLLM)")

    # Database
    db_name: str = "oskour"
    db_user: str = "GJV"
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 5432
    database_url: str = ""

    # Security
    jwt_secret_key: str = Field(default=None)

    # OpenAI-compatible API (pour mode API)
    openai_api_key: str = Field(default=None)
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = Field(default="https://api.openai.com/v1")
    openai_timeout: int = 120

    # Vision (Pixtral) pour images
    mistral_api_key: Optional[str] = Field(default=None)
    mistral_model: Optional[str] = None  # compatibilité legacy
    vision_model: str = Field(
        default="pixtral-large-latest",
        validation_alias=AliasChoices("VISION_MODEL", "VISION_API_MODEL", "PIXTRAL_MODEL"),
        description="Nom du modèle de vision utilisé en mode API",
    )
    vision_api_url: str = Field(
        default="https://api.mistral.ai/v1/chat/completions",
        validation_alias=AliasChoices("VISION_API_URL"),
        description="Endpoint compatible OpenAI pour le modèle de vision en mode API",
    )
    vision_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("VISION_API_KEY", "MISTRAL_API_KEY"),
        description="Clé API pour le modèle de vision en mode API",
    )

    # vLLM Configuration (pour mode local)
    vllm_api_url: str = "http://0.0.0.0:5263/v1/chat/completions"
    vllm_model_name: str = "Mistral-Small-3.1-24B-Instruct-2503"
    vllm_max_tokens: int = 6000
    vllm_temperature: float = 0.0
    vllm_timeout: int = 500  # secondes

    # Vision vLLM Configuration (pour mode local avec images)
    vision_vllm_url: str = Field(
        default="http://localhost:8085/v1/chat/completions",
        validation_alias=AliasChoices("VISION_VLLM_URL", "PIXTRAL_VLLM_URL"),
    )
    vision_vllm_model: str = Field(
        default="pixtral-large-latest",
        validation_alias=AliasChoices("VISION_VLLM_MODEL", "PIXTRAL_VLLM_MODEL"),
    )

    # SSL pour les appels LLM (vLLM, Pixtral, etc.)
    llm_verify_ssl: bool = Field(
        default=True,
        description="Vérifie les certificats SSL pour les appels HTTP vers les LLM (définissable via LLM_VERIFY_SSL).",
    )

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
    pdf_use_vision_threshold: int = Field(
        default=100,
        validation_alias=AliasChoices("PDF_USE_VISION_THRESHOLD", "PDF_USE_PIXTRAL_THRESHOLD"),
        description="Basculer vers le modèle de vision si le texte extrait est inférieur au seuil",
    )
    pdf_max_pages_vision: int = Field(
        default=0,
        validation_alias=AliasChoices("PDF_MAX_PAGES_VISION", "PDF_MAX_PAGES_PIXTRAL"),
        description="Nombre max de pages PDF à analyser avec le modèle de vision (0 = pas de limite)",
    )

    # Embeddings / RAG
    embedding_provider: str = "openai"  # valeurs supportées: "openai", "mistral", "local"
    embedding_model: str = "text-embedding-3-small"
    embedding_local_model_path: Optional[str] = None
    embedding_dimension: int = 1536
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
            except Exception:
                pass

        if not self.database_url:
            self.database_url = f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

        if not self.jwt_secret_key:
            self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
            if not self.jwt_secret_key:
                raise ValueError("JWT_SECRET_KEY environment variable is required")

        # Validation selon le mode
        if self.llm_mode == "api":
            if not self.openai_api_key:
                self.openai_api_key = os.getenv("OPENAI_API_KEY")
                if not self.openai_api_key:
                    raise ValueError("OPENAI_API_KEY environment variable is required in API mode")
            env_base_url = os.getenv("OPENAI_BASE_URL")
            if env_base_url:
                self.openai_base_url = env_base_url
            env_model = os.getenv("OPENAI_MODEL")
            if env_model:
                self.openai_model = env_model
            env_timeout = os.getenv("OPENAI_TIMEOUT")
            if env_timeout:
                try:
                    self.openai_timeout = int(env_timeout)
                except ValueError:
                    raise ValueError("OPENAI_TIMEOUT must be an integer (seconds)") from None

            # Vision config (Pixtral)
            if not self.mistral_api_key:
                self.mistral_api_key = os.getenv("MISTRAL_API_KEY")
            if not self.vision_api_key:
                self.vision_api_key = self.mistral_api_key
            if not self.vision_api_key:
                raise ValueError("VISION_API_KEY (ou MISTRAL_API_KEY) est requis pour le modèle de vision en mode API")
            if not self.vision_api_url:
                raise ValueError("VISION_API_URL est requis en mode API")

        elif self.llm_mode == "local":
            # En mode local, vérifier que l'URL vLLM est configurée
            if not self.vllm_api_url:
                raise ValueError("vLLM_API_URL is required in local mode")
            if not self.vision_vllm_url:
                raise ValueError("VISION_VLLM_URL is required in local mode")
            logger.info("Running in LOCAL mode with vLLM at %s", self.vllm_api_url)

        # Synchroniser provider d'embeddings avec le mode LLM si explicite
        env_provider = os.getenv("EMBEDDING_PROVIDER")
        if env_provider is None:
            self.embedding_provider = "local" if self.llm_mode == "local" else "openai"

        env_model = os.getenv("EMBEDDING_MODEL")
        if env_model is None and self.embedding_provider == "openai":
            self.embedding_model = "text-embedding-3-small"
        elif env_model is None and self.embedding_provider == "mistral":
            self.embedding_model = "mistral-embed"

        if self.embedding_provider == "local":
            if not self.embedding_local_model_path:
                raise ValueError(
                    "EMBEDDING_LOCAL_MODEL_PATH is required when EMBEDDING_PROVIDER=local"
                )
        elif self.embedding_provider not in {"openai", "mistral"}:
            raise ValueError(
                "Unsupported EMBEDDING_PROVIDER. Use 'openai', 'mistral' or 'local'."
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
logger.info("Configuration loaded: LLM Mode = %s", settings.llm_mode)
if settings.is_local_mode:
    logger.info("vLLM URL: %s", settings.vllm_api_url)
    logger.info("Model: %s", settings.vllm_model_name)
    logger.info("Vision vLLM URL: %s", settings.vision_vllm_url)
    logger.info("Vision vLLM Model: %s", settings.vision_vllm_model)
else:
    logger.info("OpenAI Model: %s", settings.openai_model)
    logger.info("OpenAI Base URL: %s", settings.openai_base_url)
    logger.info("Vision Model (API): %s", settings.vision_model)
    logger.info("Vision API URL: %s", settings.vision_api_url)
