import time
import json
from typing import List, Dict, AsyncGenerator, Tuple, Optional, Any
from app.config import settings
from app.utils.exceptions import ExternalServiceError
import logging
import httpx

logger = logging.getLogger(__name__)

class MistralService:
    def __init__(self):
        # Service générique pour une API de chat OpenAI-compatible
        self.model = settings.mistral_model
        self._api_url = settings.api_url
        self._api_key = settings.api_key
        self._timeout = 60.0

        logger.info("API LLM service initialized in API mode with URL: %s", self._api_url)
    
    async def generate_response(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> str:
        """Génération simple (non-streaming) via API OpenAI-compatible"""
        try:
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }

            payload: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
            }

            if temperature is not None:
                payload["temperature"] = max(0.0, min(1.0, float(temperature)))
            
            # Ajouter les outils si fournis
            if tools:
                payload["tools"] = tools
                if tool_choice:
                    payload["tool_choice"] = {
                        "type": "function",
                        "function": {"name": tool_choice},
                    }
                else:
                    payload["tool_choice"] = "auto"

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._api_url, json=payload, headers=headers)

            if response.status_code != 200:
                error_msg = f"LLM API request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise ExternalServiceError("LLM API", Exception(error_msg))

            result = response.json()
            choices = result.get("choices") or []
            if not choices:
                logger.warning("LLM API returned no choices")
                return "Je n'ai pas pu traiter votre demande. Veuillez réessayer."

            message = choices[0].get("message") or {}

            # Gérer les appels d'outils
            tool_calls = message.get("tool_calls") or []
            if tool_calls:
                logger.info(
                    "Tool calls detected: %s",
                    [tc.get("function", {}).get("name") for tc in tool_calls],
                )
                return await self._handle_tool_calls(tool_calls, messages)

            # Si pas de contenu, retourner un message par défaut
            content = message.get("content")
            if not content:
                logger.warning("LLM API returned empty content without tool calls")
                return "Je n'ai pas pu traiter votre demande. Veuillez réessayer."

            return content

        except httpx.TimeoutException:
            logger.error("LLM API request timed out after %.1fs", self._timeout)
            raise ExternalServiceError("LLM API", Exception("Request timeout"))
        except Exception as e:
            logger.error("LLM API error: %s", e)
            raise ExternalServiceError("LLM API", e)
    
    async def _handle_tool_calls(self, tool_calls: List[Any], original_messages: List[Dict]) -> str:
        """Handle tool calls from API LLM response (format OpenAI-compatible)."""
        try:
            from app.services.mcp_service import get_mcp_service
            mcp_service = get_mcp_service()
            
            # Handle the first tool call (for now, we'll handle one at a time)
            tool_call = tool_calls[0] if tool_calls else None
            function = (tool_call or {}).get("function") if isinstance(tool_call, dict) else None
            function_name = function.get("name") if isinstance(function, dict) else None

            if not function_name:
                logger.error("Tool call received without function name")
                return "Erreur lors de l'exécution de l'outil : fonction inconnue."
            
            if function_name == "generate_powerpoint_from_text":
                # Parse the arguments
                raw_args = function.get("arguments")
                if isinstance(raw_args, str):
                    arguments = json.loads(raw_args)
                else:
                    arguments = raw_args or {}
                
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
            
            return f"Outil {function_name} appelé avec les arguments : {function.get('arguments') if function else '{}'}"
            
        except Exception as e:
            logger.error("Tool call handling error: %s", e)
            return f"Erreur lors de l'exécution de l'outil : {str(e)}"
    
    async def generate_response_with_metadata(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> Tuple[str, Dict]:
        """Génération avec métadonnées de performance via API OpenAI-compatible"""
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }

            payload: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
            }

            if temperature is not None:
                payload["temperature"] = max(0.0, min(1.0, float(temperature)))
            
            # Ajouter les outils si fournis
            if tools:
                logger.info("LLM API: Calling with %d tool(s)", len(tools))
                payload["tools"] = tools
                if tool_choice:
                    payload["tool_choice"] = {
                        "type": "function",
                        "function": {"name": tool_choice},
                    }
                else:
                    payload["tool_choice"] = "auto"
            else:
                logger.info("LLM API: No tools provided")

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._api_url, json=payload, headers=headers)

            if response.status_code != 200:
                error_msg = f"LLM API request with metadata failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise ExternalServiceError("LLM API", Exception(error_msg))

            result = response.json()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            usage = result.get("usage", {})

            metadata = {
                "model_used": self.model,
                "tokens_used": usage.get("total_tokens"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "processing_time": processing_time,
                "temperature": payload.get("temperature", 0.7),
                "tools_used": bool(tools),
            }
            
            choices = result.get("choices") or []
            if not choices:
                logger.warning("LLM API returned no choices with metadata")
                return "Je n'ai pas pu traiter votre demande. Veuillez réessayer.", metadata

            message = choices[0].get("message") or {}

            # Gérer les appels d'outils
            tool_calls = message.get("tool_calls") or []
            if tool_calls:
                metadata["tool_calls"] = [tc.get("function", {}).get("name") for tc in tool_calls]
                content = await self._handle_tool_calls(tool_calls, messages)
                return content, metadata

            content = message.get("content")
            if not content:
                logger.warning("LLM API returned empty content without tool calls (metadata)")
                return "Je n'ai pas pu traiter votre demande. Veuillez réessayer.", metadata

            return content, metadata

        except Exception as e:
            logger.error("LLM API error with metadata: %s", e)
            raise ExternalServiceError("LLM API", e)
    
    async def generate_stream_response(
        self, 
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Génération en streaming pour SSE via API OpenAI-compatible"""
        try:
            # Pour le streaming avec outils, on va d'abord générer normalement puis streamer le résultat
            if tools:
                # D'abord envoyer un signal indiquant que nous vérifions les outils
                yield "[[TOOL_CHECK]]"
                
                # Les outils ne sont pas compatibles avec le streaming pour l'instant
                # On génère le résultat puis on le "stream" artificiellement
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
            
            # Streaming direct via l'API LLM (SSE en format OpenAI-compatible)
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            }

            payload: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "stream": True,
            }

            if temperature is not None:
                payload["temperature"] = max(0.0, min(1.0, float(temperature)))

            if tool_choice:
                payload["tool_choice"] = tool_choice

            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", self._api_url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        error_msg = f"LLM API streaming failed with status {response.status_code}: {response.text}"
                        logger.error(error_msg)
                        raise ExternalServiceError("LLM API", Exception(error_msg))

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        if line.startswith(":"):
                            # Comment/heartbeat from SSE, skip it
                            continue

                        if not line.startswith("data:"):
                            continue

                        data = line[5:].strip()
                        if not data:
                            continue

                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            logger.warning("LLM API streaming: unable to decode chunk: %s", data)
                            continue

                        choices = chunk.get("choices") or []
                        if not choices:
                            continue

                        delta = choices[0].get("delta") or {}
                        content_piece = delta.get("content")
                        if content_piece:
                            yield content_piece
        except Exception as e:
            logger.error("LLM API streaming error: %s", e)
            raise ExternalServiceError("LLM API", e)
