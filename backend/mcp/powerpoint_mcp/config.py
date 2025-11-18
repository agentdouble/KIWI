"""Configuration management for the PowerPoint JSON generator."""

import os
from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MistralConfig(BaseModel):
    """Mistral API configuration."""
    api_key: str = Field(default_factory=lambda: os.getenv("MISTRAL_API_KEY", ""))
    model: str = Field(default="mistral-small-latest")
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
        """Check if Mistral API key is configured."""
        return bool(self.mistral.api_key)
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create config from environment variables."""
        return cls(
            mistral=MistralConfig(
                api_key=os.getenv("MISTRAL_API_KEY", ""),
                model=os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
                temperature=float(os.getenv("MISTRAL_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("MISTRAL_MAX_TOKENS", "128000")),
                mode=os.getenv("MISTRAL_MODE", "api"),
                local_base_url=os.getenv("LOCAL_BASE_URL", "http://localhost:5263/v1"),
                local_model_path=os.getenv("LOCAL_MODEL_PATH", "/home/llama/models/base_models/Mistral-Small-3.1-24B-Instruct-2503")
            ),
            output=OutputConfig(
                pretty_json=os.getenv("OUTPUT_PRETTY_JSON", "true").lower() == "true",
                indent=int(os.getenv("OUTPUT_INDENT", "2")),
                output_dir=Path(os.getenv("OUTPUT_DIR", "output"))
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO")
            ),
            debug=os.getenv("DEBUG", "false").lower() == "true"
        )


# Global config instance
config = AppConfig.from_env()