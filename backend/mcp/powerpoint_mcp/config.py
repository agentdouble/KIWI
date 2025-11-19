"""Configuration management for the PowerPoint JSON generator."""

import os
from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from a local .env when running standalone
load_dotenv()

try:
    # When running inside the FoyerGPT backend, reuse its settings
    from app.config import settings as backend_settings  # type: ignore
except Exception:
    backend_settings = None


class MistralConfig(BaseModel):
    """LLM API configuration for the PowerPoint MCP (OpenAI-compatible)."""
    api_key: str = Field(default="")
    api_url: str = Field(default="https://api.mistral.ai/v1/chat/completions")
    api_model: str = Field(default="mistral-small-latest")
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    max_tokens: int = Field(default=128000, ge=1)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    timeout: int = Field(default=180)  # 3 minutes pour permettre la génération de longs contenus
    retry_attempts: int = Field(default=3)
    retry_delay: float = Field(default=1.0)
    
    # Mode: api or local
    mode: Literal["api", "local"] = Field(default="api")
    
    # Local LLM configuration
    local_base_url: str = Field(default="http://localhost:5263/v1")
    local_model_path: str = Field(default="/home/llama/models/base_models/Mistral-Small-3.1-24B-Instruct-2503")


class OutputConfig(BaseModel):
    """Output configuration."""
    pretty_json: bool = Field(default=True)
    indent: int = Field(default=2)
    output_dir: Path = Field(default_factory=lambda: Path("output"))
    save_intermediate: bool = Field(default=False)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO")
    format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
                "<level>{message}</level>"
    )
    file: Optional[Path] = Field(default=None)
    rotation: str = Field(default="10 MB")
    retention: str = Field(default="7 days")


class AppConfig(BaseModel):
    """Application configuration."""
    mistral: MistralConfig = Field(default_factory=MistralConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    def validate_api_key(self) -> bool:
        """Check if LLM API key is configured."""
        return bool(self.mistral.api_key)
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """
        Create config from environment variables.
        
        When running inside the FoyerGPT backend, reuse its LLM configuration
        (mode, API key, local vLLM URL, model name) so it is defined only once
        in backend/.env. When running standalone, fall back to local env vars.
        """
        # Integrated mode: reuse backend settings
        if backend_settings is not None:
            from urllib.parse import urlparse, urlunparse

            mode: Literal["api", "local"] = "local" if backend_settings.is_local_mode else "api"

            # Derive local_base_url from the backend vLLM API URL, matching MCP service behaviour
            local_base_url = "http://localhost:5263/v1"
            vllm_url = getattr(backend_settings, "vllm_api_url", None)
            if vllm_url:
                try:
                    parsed = urlparse(vllm_url)
                    base_path = parsed.path
                    if base_path.endswith("/chat/completions"):
                        base_path = base_path[: -len("/chat/completions")]
                    if not base_path:
                        base_path = "/"
                    local_base_url = urlunparse(parsed._replace(path=base_path))
                except Exception:
                    # Keep default local_base_url; backend settings validation already guards vLLM config
                    pass

            # For API mode, reuse the generic LLM API configuration from backend settings
            api_key = getattr(backend_settings, "api_key", "") or ""
            api_url = getattr(backend_settings, "api_url", "https://api.mistral.ai/v1/chat/completions")
            api_model = getattr(backend_settings, "api_model", "mistral-small-latest")

            if mode == "api" and not api_key:
                raise ValueError("API_KEY is required in API mode for PowerPoint configuration")

            mistral = MistralConfig(
                api_key=api_key,
                api_url=api_url,
                api_model=api_model,
                temperature=float(os.getenv("MISTRAL_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("MISTRAL_MAX_TOKENS", "128000")),
                mode=mode,
                local_base_url=local_base_url,
                local_model_path=getattr(
                    backend_settings,
                    "vllm_model_name",
                    MistralConfig().local_model_path,
                ),
            )
        else:
            # Standalone mode: use local environment variables
            mistral = MistralConfig(
                api_key=os.getenv("API_KEY", ""),
                api_url=os.getenv("API_URL", "https://api.mistral.ai/v1/chat/completions"),
                api_model=os.getenv("API_MODEL", "mistral-small-latest"),
                temperature=float(os.getenv("MISTRAL_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("MISTRAL_MAX_TOKENS", "128000")),
                mode=os.getenv("MISTRAL_MODE", "api"),
                local_base_url=os.getenv("LOCAL_BASE_URL", "http://localhost:5263/v1"),
                local_model_path=os.getenv(
                    "LOCAL_MODEL_PATH",
                    "/home/llama/models/base_models/Mistral-Small-3.1-24B-Instruct-2503",
                ),
            )

        return cls(
            mistral=mistral,
            output=OutputConfig(
                pretty_json=os.getenv("OUTPUT_PRETTY_JSON", "true").lower() == "true",
                indent=int(os.getenv("OUTPUT_INDENT", "2")),
                output_dir=Path(os.getenv("OUTPUT_DIR", "output")),
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO")
            ),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )


# Global config instance
config = AppConfig.from_env()
