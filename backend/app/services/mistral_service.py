import os
import time
import asyncio
import json
from mistralai import Mistral
from typing import List, Dict, AsyncGenerator, Tuple, Optional, Any
from app.config import settings
from app.utils.exceptions import ExternalServiceError
import logging
import httpx

logger = logging.getLogger(__name__)

class MistralService:
    def __init__(self):
        self.client = Mistral(api_key=settings.mistral_api_key)
        self.model = settings.mistral_model
        self._api_url = "https://api.mistral.ai/v1/chat/completions"
    
    async def generate_response(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> str:
        """Génération simple (non-streaming) - Vraiment asynchrone"""
        try:
            # Préparer les paramètres pour l'API Mistral
            api_params = {
                "model": self.model,
                "messages": messages
            }
            if temperature is not None:
                api_params["temperature"] = max(0.0, min(1.0, float(temperature)))
            
            # Ajouter les outils si fournis
            if tools:
                api_params["tools"] = tools
                if tool_choice:
                    api_params["tool_choice"] = {
                        "type": "function",
                        "function": {"name": tool_choice},
                    }
                else:
                    api_params["tool_choice"] = "auto"
            
            # Exécuter l'appel synchrone dans un thread séparé
            response = await asyncio.to_thread(
                self.client.chat.complete,
                **api_params
            )
            
            # Gérer les appels d'outils
            message = response.choices[0].message
            
            if message.tool_calls:
                logger.info(f"Tool calls detected: {[tc.function.name for tc in message.tool_calls]}")
                return await self._handle_tool_calls(message.tool_calls, messages)
            
            # Si pas de contenu, retourner un message par défaut
            if not message.content:
                logger.warning("Mistral returned empty content without tool calls")
                return "Je n'ai pas pu traiter votre demande. Veuillez réessayer."
            
            return message.content
            
        except Exception as e:
            logger.error(f"Mistral API error: {str(e)}")
            raise ExternalServiceError("Mistral AI", e)
    
    async def _handle_tool_calls(self, tool_calls: List[Any], original_messages: List[Dict]) -> str:
        """Handle tool calls from Mistral API response."""
        try:
            from app.services.mcp_service import get_mcp_service
            mcp_service = get_mcp_service()
            
            # Handle the first tool call (for now, we'll handle one at a time)
            tool_call = tool_calls[0]
            function_name = tool_call.function.name
            
            if function_name == "generate_powerpoint_from_text":
                # Parse the arguments
                arguments = json.loads(tool_call.function.arguments)
                
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
            
            return f"Outil {function_name} appelé avec les arguments : {tool_call.function.arguments}"
            
        except Exception as e:
            logger.error(f"Tool call handling error: {e}")
            return f"Erreur lors de l'exécution de l'outil : {str(e)}"
    
    async def generate_response_with_metadata(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> Tuple[str, Dict]:
        """Génération avec métadonnées de performance - Vraiment asynchrone"""
        start_time = time.time()
        
        try:
            # Préparer les paramètres pour l'API Mistral
            api_params = {
                "model": self.model,
                "messages": messages
            }
            if temperature is not None:
                api_params["temperature"] = max(0.0, min(1.0, float(temperature)))
            
            # Ajouter les outils si fournis
            if tools:
                logger.info(f"Mistral: Calling with {len(tools)} tool(s)")
                api_params["tools"] = tools
                if tool_choice:
                    api_params["tool_choice"] = {
                        "type": "function",
                        "function": {"name": tool_choice},
                    }
                else:
                    api_params["tool_choice"] = "auto"
            else:
                logger.info("Mistral: No tools provided")
            
            # Exécuter l'appel synchrone dans un thread séparé
            response = await asyncio.to_thread(
                self.client.chat.complete,
                **api_params
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            metadata = {
                "model_used": self.model,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None,
                "processing_time": processing_time,
                "temperature": api_params.get("temperature", 0.7),
                "tools_used": bool(tools),
            }
            
            # Gérer les appels d'outils
            message = response.choices[0].message
            
            if message.tool_calls:
                metadata["tool_calls"] = [tc.function.name for tc in message.tool_calls]
                content = await self._handle_tool_calls(message.tool_calls, messages)
                return content, metadata
            
            return message.content, metadata
            
        except Exception as e:
            logger.error(f"Mistral API error with metadata: {str(e)}")
            raise ExternalServiceError("Mistral AI", e)
    
    async def generate_stream_response(
        self, 
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Génération en streaming pour SSE - Vraiment asynchrone"""
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
            
            # Streaming direct via l'API Mistral (SSE officielles)
            headers = {
                "Authorization": f"Bearer {settings.mistral_api_key}",
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
                        error_msg = f"Mistral streaming failed with status {response.status_code}: {response.text}"
                        logger.error(error_msg)
                        raise ExternalServiceError("Mistral AI", Exception(error_msg))

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
                            logger.warning("Mistral streaming: unable to decode chunk: %s", data)
                            continue

                        choices = chunk.get("choices") or []
                        if not choices:
                            continue

                        delta = choices[0].get("delta") or {}
                        content_piece = delta.get("content")
                        if content_piece:
                            yield content_piece
        except Exception as e:
            logger.error(f"Mistral streaming API error: {str(e)}")
            raise ExternalServiceError("Mistral AI", e)
