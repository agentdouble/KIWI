import asyncio
import httpx
import time
from typing import List, Dict, AsyncGenerator, Tuple, Optional
from urllib.parse import urlparse, urlunparse
from app.config import settings
from app.utils.exceptions import ExternalServiceError
import logging
import json

logger = logging.getLogger(__name__)

class VLLMService:
    """Service pour interagir avec vLLM en mode local"""
    
    def __init__(self):
        self.api_url = self._normalize_client_url(
            settings.vllm_api_url,
            label="vLLM",
        )
        self.model_name = settings.vllm_model_name
        self.max_tokens = settings.vllm_max_tokens
        self.temperature = settings.vllm_temperature
        self.timeout = settings.vllm_timeout

        # Configuration vision pour le mode local
        self.vision_url = self._normalize_client_url(
            settings.vision_vllm_url,
            label="Vision vLLM",
        )
        self.vision_model = settings.vision_vllm_model
        
        logger.info(f"vLLM Service initialized with URL: {self.api_url}")
        logger.info(f"Vision vLLM available at: {self.vision_url}")
        logger.info(f"Vision vLLM model configured as: {self.vision_model}")

        # Contrôle de la vérification SSL pour les appels HTTP vers les LLM
        self.verify_ssl = settings.llm_verify_ssl
        
        logger.info(
            "LLM SSL verification is %s",
            "ENABLED" if self.verify_ssl else "DISABLED",
        )

    @staticmethod
    def _normalize_client_url(url: str, *, label: str) -> str:
        if not url:
            return url

        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        new_host = hostname

        if hostname in {"0.0.0.0", "::", ""}:
            new_host = "localhost"
        elif hostname.endswith(".local"):
            new_host = "localhost"

        if new_host != hostname:
            username = parsed.username or ""
            password = parsed.password or ""
            port = parsed.port

            auth_part = ""
            if username:
                auth_part = username
                if password:
                    auth_part += f":{password}"
                auth_part += "@"

            if port is not None:
                new_netloc = f"{auth_part}{new_host}:{port}"
            else:
                new_netloc = f"{auth_part}{new_host}"

            logger.warning(
                "%s URL host '%s' is not reachable from client; using '%s' instead",
                label,
                hostname or "<empty>",
                new_host,
            )
            parsed = parsed._replace(netloc=new_netloc)
        return urlunparse(parsed)

    async def _sync_vision_model(self, client: httpx.AsyncClient) -> None:
        """Vérifie que le modèle de vision configuré est disponible côté vLLM."""
        try:
            list_url = self.vision_url.replace("/chat/completions", "/models")
            response = await client.get(list_url)
            response.raise_for_status()

            payload = response.json()
            available_models = [model.get("id") for model in payload.get("data", []) if model.get("id")]

            if not available_models:
                raise ExternalServiceError(
                    "Vision vLLM",
                    Exception("Aucun modèle de vision disponible sur le serveur local"),
                )

            if self.vision_model not in available_models:
                raise ExternalServiceError(
                    "Vision vLLM",
                    Exception(
                        "Le modèle de vision configuré (%s) est introuvable. Modèles disponibles: %s"
                        % (self.vision_model, ", ".join(available_models)),
                    ),
                )
        except Exception as exc:
            logger.error("Impossible de synchroniser les modèles de vision vLLM: %s", exc)
            raise
    
    async def _handle_tool_calls(self, tool_calls: List[Dict], original_messages: List[Dict]) -> str:
        """Handle tool calls from vLLM response."""
        try:
            from app.services.mcp_service import get_mcp_service
            mcp_service = get_mcp_service()
            
            # Handle the first tool call (for now, we'll handle one at a time)
            tool_call = tool_calls[0]
            function_name = tool_call["function"]["name"]
            
            if function_name == "generate_powerpoint_from_text":
                # Parse the arguments
                arguments = json.loads(tool_call["function"]["arguments"]) if isinstance(tool_call["function"]["arguments"], str) else tool_call["function"]["arguments"]
                
                # Execute the tool asynchronously
                result = await mcp_service.execute_tool(function_name, arguments)
                
                # Format the response for the user
                if result.get("success"):
                    response = f"✅ {result['message']}\n\n"
                    
                    # Extract details from mcp_details if available
                    details = result.get('mcp_details', {})
                    
                    response += f"📊 **Présentation créée** : {details.get('title', 'Sans titre')}\n"
                    response += f"📄 **Nombre de slides** : {details.get('total_slides', 'N/A')}\n"
                    response += f"📁 **Fichier** : {details.get('filename', 'presentation.pptx')}\n"
                    
                    if details.get('download_url'):
                        response += f"\n💾 [Télécharger la présentation]({details['download_url']})"
                    
                    return response
                else:
                    return f"❌ {result.get('message', 'Erreur lors de la génération')}"
            
            return f"Outil {function_name} appelé avec les arguments : {tool_call['function']['arguments']}"
            
        except Exception as e:
            logger.error(f"Tool call handling error: {e}")
            return f"Erreur lors de l'exécution de l'outil : {str(e)}"
    
    async def generate_response(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> str:
        """Génération simple (non-streaming) avec vLLM"""
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": (max(0.0, min(1.0, float(temperature))) if temperature is not None else self.temperature)
        }
        
        if tools is not None:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = {
                    "type": "function",
                    "function": {"name": tool_choice},
                }
            else:
                payload["tool_choice"] = "auto"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
                logger.debug(f"Sending request to vLLM: {json.dumps(payload, indent=2)[:500]}...")
                response = await client.post(self.api_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    message = result["choices"][0]["message"]
                    
                    # Gérer les appels d'outils
                    if "tool_calls" in message and message["tool_calls"]:
                        logger.info(f"Tool calls detected in vLLM response: {[tc['function']['name'] for tc in message['tool_calls']]}")
                        return await self._handle_tool_calls(message["tool_calls"], messages)
                    
                    # Si pas de contenu, retourner un message par défaut
                    if not message.get("content"):
                        logger.warning("vLLM returned empty content without tool calls")
                        return "Je n'ai pas pu traiter votre demande. Veuillez réessayer."
                    
                    return message["content"]
                else:
                    error_msg = f"vLLM request failed with status {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    raise ExternalServiceError("vLLM", Exception(error_msg))
                    
        except httpx.TimeoutException:
            logger.error(f"vLLM request timed out after {self.timeout}s")
            raise ExternalServiceError("vLLM", Exception("Request timeout"))
        except Exception as e:
            logger.error(f"vLLM API error: {str(e)}")
            raise ExternalServiceError("vLLM", e)
    
    async def generate_response_with_metadata(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> Tuple[str, Dict]:
        """Génération avec métadonnées de performance"""
        start_time = time.time()
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": (max(0.0, min(1.0, float(temperature))) if temperature is not None else self.temperature)
        }
        
        if tools is not None:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = {
                    "type": "function",
                    "function": {"name": tool_choice},
                }
            else:
                payload["tool_choice"] = "auto"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
                response = await client.post(self.api_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    end_time = time.time()
                    processing_time = end_time - start_time
                    
                    # Extraire les métadonnées de la réponse vLLM
                    usage = result.get("usage", {})
                    metadata = {
                        "model_used": self.model_name,
                        "tokens_used": usage.get("total_tokens", None),
                        "prompt_tokens": usage.get("prompt_tokens", None),
                        "completion_tokens": usage.get("completion_tokens", None),
                        "processing_time": processing_time,
                        "temperature": payload["temperature"],
                        "mode": "local",
                        "tools_used": bool(tools)
                    }
                    
                    message = result["choices"][0]["message"]
                    
                    # Gérer les appels d'outils
                    if "tool_calls" in message and message["tool_calls"]:
                        metadata["tool_calls"] = [tc["function"]["name"] for tc in message["tool_calls"]]
                        content = await self._handle_tool_calls(message["tool_calls"], messages)
                        return content, metadata
                    
                    # Si pas de contenu, retourner un message par défaut
                    if not message.get("content"):
                        logger.warning("vLLM returned empty content without tool calls")
                        return "Je n'ai pas pu traiter votre demande. Veuillez réessayer.", metadata
                    
                    return message["content"], metadata
                else:
                    error_msg = f"vLLM request failed with status {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    raise ExternalServiceError("vLLM", Exception(error_msg))
                    
        except Exception as e:
            logger.error(f"vLLM API error with metadata: {str(e)}")
            raise ExternalServiceError("vLLM", e)
    
    async def generate_stream_response(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Génération en streaming pour SSE avec vLLM"""
        # Si des outils sont fournis, on ne peut pas faire de streaming direct
        # On doit d'abord obtenir la réponse complète pour vérifier les tool calls
        if tools:
            # D'abord envoyer un signal indiquant que nous vérifions les outils
            yield "[[TOOL_CHECK]]"
            
            # Générer la réponse complète
            content, metadata = await self.generate_response_with_metadata(
                messages,
                tools,
                temperature=temperature,
                tool_choice=tool_choice,
            )
            
            # Si PowerPoint a été utilisé, envoyer un signal
            if metadata.get("tool_calls") and "generate_powerpoint_from_text" in metadata["tool_calls"]:
                yield "[[POWERPOINT_GENERATION]]"
            
            # Retourner le contenu en une seule fois pour éviter un faux streaming
            if content:
                yield content
            return
        
        # Streaming normal sans outils
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": (max(0.0, min(1.0, float(temperature))) if temperature is not None else self.temperature),
            "stream": True  # Activer le streaming
        }
        
        try:
            async with httpx.AsyncClient(timeout=None, verify=self.verify_ssl) as client:  # Pas de timeout global pour le streaming
                async with client.stream('POST', self.api_url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        error_msg = f"vLLM streaming failed with status {response.status_code}"
                        logger.error(error_msg)
                        raise ExternalServiceError("vLLM", Exception(error_msg))
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Enlever "data: "
                            if data == "[DONE]":
                                break
                            
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    delta = chunk["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse streaming chunk: {data}")
                                continue
                            
        except Exception as e:
            logger.error(f"vLLM streaming API error: {str(e)}")
            raise ExternalServiceError("vLLM", e)
    
    async def process_image_with_vision_model(self, image_base64: str, prompt: str = "Décris cette image en détail.") -> str:
        """
        Traiter une image avec le modèle de vision en mode local (vLLM)
        """
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "model": self.vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                    ]
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        try:
            timeout = httpx.Timeout(self.timeout, connect=min(10.0, float(self.timeout)))
            async with httpx.AsyncClient(timeout=timeout, verify=self.verify_ssl) as client:
                await self._sync_vision_model(client)
                payload["model"] = self.vision_model

                logger.info(
                    "Sending image to vision vLLM at %s with model %s (timeout=%ss)",
                    self.vision_url,
                    self.vision_model,
                    self.timeout,
                )

                try:
                    async with asyncio.timeout(self.timeout):
                        response = await client.post(self.vision_url, json=payload, headers=headers)
                except TimeoutError:
                    logger.error(
                        "Vision vLLM request timed out after %ss at %s",
                        self.timeout,
                        self.vision_url,
                    )
                    raise ExternalServiceError(
                        "Vision vLLM",
                        Exception(f"Request timed out after {self.timeout}s"),
                    )
                except httpx.ConnectError as conn_err:
                    logger.error(
                        "Vision vLLM connection failed at %s: %s",
                        self.vision_url,
                        conn_err,
                    )
                    raise ExternalServiceError(
                        "Vision vLLM",
                        Exception(
                            "Impossible de se connecter au serveur de modèle de vision local. "
                            "Assurez-vous qu'il est démarré et accessible."
                        ),
                    )

                if response.status_code == 404 and "does not exist" in response.text:
                    await self._sync_vision_model(client)
                    payload["model"] = self.vision_model
                    logger.info(
                        "Retrying vision vLLM request with resolved model %s",
                        self.vision_model,
                    )
                    async with asyncio.timeout(self.timeout):
                        response = await client.post(self.vision_url, json=payload, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"].get("content", "")
                    if isinstance(content, list):
                        content = "".join(
                            part.get("text", "") if isinstance(part, dict) else str(part)
                            for part in content
                            if part is not None
                        )
                    logger.info("Successfully processed image with vision vLLM")
                    return content

                error_msg = (
                    f"Vision vLLM request failed with status {response.status_code}: {response.text}"
                )
                logger.error(error_msg)
                raise ExternalServiceError("Vision vLLM", Exception(error_msg))

        except httpx.TimeoutException:
            logger.error(f"Vision vLLM request timed out after {self.timeout}s")
            raise ExternalServiceError("Vision vLLM", Exception("Request timeout"))
        except Exception as e:
            logger.error(f"Vision vLLM API error: {str(e)}")
            raise ExternalServiceError("Vision vLLM", e)
    
    async def health_check(self) -> bool:
        """Vérifier que le serveur vLLM est accessible"""
        try:
            # Essayer l'endpoint /health ou /v1/models selon vLLM
            health_url = self.api_url.replace("/chat/completions", "/models")
            async with httpx.AsyncClient(timeout=5.0, verify=self.verify_ssl) as client:
                response = await client.get(health_url)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"vLLM health check failed: {str(e)}")
            return False
            
    async def vision_health_check(self) -> bool:
        """Vérifier que le serveur de modèle de vision vLLM est accessible"""
        try:
            health_url = self.vision_url.replace("/chat/completions", "/models")
            async with httpx.AsyncClient(timeout=5.0, verify=self.verify_ssl) as client:
                response = await client.get(health_url)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Vision vLLM health check failed: {str(e)}")
            return False
