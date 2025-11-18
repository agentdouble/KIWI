from typing import List, Dict, AsyncGenerator, Tuple, Optional
from app.config import settings
from app.services.mistral_service import MistralService
from app.services.vllm_service import VLLMService
import logging

logger = logging.getLogger(__name__)

class LLMService:
    """Service abstrait qui utilise soit Mistral API soit vLLM selon la configuration"""
    
    def __init__(self):
        if settings.is_api_mode:
            logger.info("🌐 Initializing LLM Service in API mode (Mistral)")
            self._service = MistralService()
            self.mode = "api"
        else:
            logger.info("🖥️ Initializing LLM Service in LOCAL mode (vLLM)")
            self._service = VLLMService()
            self.mode = "local"
    
    async def generate_response(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> str:
        """Génération simple (non-streaming)"""
        if self.mode == "api":
            # MistralService supporte maintenant les tools
            return await self._service.generate_response(messages, tools, temperature=temperature, tool_choice=tool_choice)
        else:
            # VLLMService supporte les tools
            return await self._service.generate_response(messages, tools, temperature=temperature, tool_choice=tool_choice)
    
    async def generate_response_with_metadata(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> Tuple[str, Dict]:
        """Génération avec métadonnées de performance"""
        if self.mode == "api":
            # MistralService supporte maintenant les tools
            response, metadata = await self._service.generate_response_with_metadata(
                messages,
                tools,
                temperature=temperature,
                tool_choice=tool_choice,
            )
            metadata["mode"] = "api"
            return response, metadata
        else:
            # VLLMService supporte les tools
            return await self._service.generate_response_with_metadata(
                messages,
                tools,
                temperature=temperature,
                tool_choice=tool_choice,
            )
    
    async def generate_stream_response(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Génération en streaming pour SSE"""
        if self.mode == "api":
            # MistralService supporte maintenant les tools
            async for chunk in self._service.generate_stream_response(
                messages,
                tools,
                temperature=temperature,
                tool_choice=tool_choice,
            ):
                yield chunk
        else:
            # VLLMService supporte les tools
            async for chunk in self._service.generate_stream_response(
                messages,
                tools,
                temperature=temperature,
                tool_choice=tool_choice,
            ):
                yield chunk
    
    @property
    def model_name(self) -> str:
        """Retourne le nom du modèle utilisé"""
        if self.mode == "api":
            return settings.mistral_model
        else:
            return settings.vllm_model_name
    
    @property
    def is_local_mode(self) -> bool:
        """Vérifie si on est en mode local"""
        return self.mode == "local"
    
    async def health_check(self) -> bool:
        """Vérifier la santé du service"""
        if self.mode == "local" and hasattr(self._service, 'health_check'):
            return await self._service.health_check()
        return True  # En mode API, on suppose que c'est OK

# Instance globale unique du service LLM
llm_service = LLMService()

def get_llm_service() -> LLMService:
    """Retourne l'instance du service LLM"""
    return llm_service
