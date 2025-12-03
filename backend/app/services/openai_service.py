import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from openai import AsyncOpenAI

from app.config import settings
from app.utils.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


def _extract_text(content: Any) -> str:
    """Normalise les contenus OpenAI (str ou liste de blocs) en texte brut."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)


class OpenAIService:
    """Client OpenAI compatible avec l'API standard (et les proxys type vLLM)."""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout,
        )
        self.model = settings.openai_model

    async def generate_response(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> str:
        """Génération simple (non-streaming)."""
        try:
            params: Dict[str, Any] = {"model": self.model, "messages": messages}
            if temperature is not None:
                params["temperature"] = max(0.0, min(1.0, float(temperature)))
            if tools:
                params["tools"] = tools
                params["tool_choice"] = tool_choice or "auto"

            response = await self.client.chat.completions.create(**params)
            message = response.choices[0].message

            if getattr(message, "tool_calls", None):
                logger.info(
                    "Tool calls detected: %s",
                    [tc.function.name for tc in message.tool_calls],
                )
                return await self._handle_tool_calls(message.tool_calls, messages)

            content = _extract_text(message.content)
            if not content:
                logger.warning("OpenAI returned empty content without tool calls")
                return "Je n'ai pas pu traiter votre demande. Veuillez réessayer."
            return content
        except Exception as exc:
            logger.error("OpenAI API error: %s", exc)
            raise ExternalServiceError("OpenAI", exc)

    async def generate_response_with_metadata(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> Tuple[str, Dict]:
        """Génération avec métadonnées de performance."""
        start_time = time.time()
        try:
            params: Dict[str, Any] = {"model": self.model, "messages": messages}
            if temperature is not None:
                params["temperature"] = max(0.0, min(1.0, float(temperature)))
            if tools:
                logger.info("OpenAI: Calling with %d tool(s)", len(tools))
                params["tools"] = tools
                params["tool_choice"] = tool_choice or "auto"
            else:
                logger.info("OpenAI: No tools provided")

            response = await self.client.chat.completions.create(**params)

            metadata = {
                "model_used": self.model,
                "tokens_used": getattr(getattr(response, "usage", None), "total_tokens", None),
                "prompt_tokens": getattr(getattr(response, "usage", None), "prompt_tokens", None),
                "completion_tokens": getattr(getattr(response, "usage", None), "completion_tokens", None),
                "processing_time": time.time() - start_time,
                "temperature": params.get("temperature", 0.7),
                "tools_used": bool(tools),
            }

            message = response.choices[0].message
            if getattr(message, "tool_calls", None):
                metadata["tool_calls"] = [tc.function.name for tc in message.tool_calls]
                content = await self._handle_tool_calls(message.tool_calls, messages)
                return content, metadata

            content = _extract_text(message.content)
            return content, metadata
        except Exception as exc:
            logger.error("OpenAI API error with metadata: %s", exc)
            raise ExternalServiceError("OpenAI", exc)

    async def _handle_tool_calls(self, tool_calls: List[Any], original_messages: List[Dict]) -> str:
        """Handle tool calls coming back from OpenAI."""
        try:
            from app.services.mcp_service import get_mcp_service

            mcp_service = get_mcp_service()
            tool_call = tool_calls[0]
            function = getattr(tool_call, "function", None) or tool_call.get("function")
            function_name = getattr(function, "name", None) or (function.get("name") if function else None)
            arguments_raw = getattr(function, "arguments", None) or (function.get("arguments") if function else None)
            arguments = json.loads(arguments_raw) if isinstance(arguments_raw, str) else (arguments_raw or {})

            if function_name == "generate_powerpoint_from_text":
                result = await mcp_service.execute_tool(function_name, arguments)
                if result.get("success"):
                    details = result.get("mcp_details", {})
                    response = f"✅ {result['message']}\n\n"
                    response += f"📊 **Présentation créée** : {details.get('title', 'Sans titre')}\n"
                    response += f"📄 **Nombre de slides** : {details.get('total_slides', 'N/A')}\n"
                    response += f"📁 **Fichier** : {details.get('filename', 'presentation.pptx')}\n"
                    if details.get("download_url"):
                        response += f"\n💾 [Télécharger la présentation]({details['download_url']})"
                    return response
                return f"❌ {result.get('message', 'Erreur lors de la génération')}"

            return f"Outil {function_name} appelé avec les arguments : {arguments}"
        except Exception as exc:
            logger.error("Tool call handling error: %s", exc)
            return f"Erreur lors de l'exécution de l'outil : {exc}"

    async def generate_stream_response(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        tool_choice: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Génération en streaming pour SSE."""
        try:
            if tools:
                yield "[[TOOL_CHECK]]"
                content, metadata = await self.generate_response_with_metadata(
                    messages,
                    tools,
                    temperature=temperature,
                    tool_choice=tool_choice,
                )
                if metadata.get("tool_calls") and "generate_powerpoint_from_text" in metadata["tool_calls"]:
                    yield "[[POWERPOINT_GENERATION]]"
                if content:
                    yield content
                return

            payload: Dict[str, Any] = {"model": self.model, "messages": messages, "stream": True}
            if temperature is not None:
                payload["temperature"] = max(0.0, min(1.0, float(temperature)))
            if tool_choice:
                payload["tool_choice"] = tool_choice

            stream = await self.client.chat.completions.create(**payload)
            async for chunk in stream:
                for choice in getattr(chunk, "choices", []) or []:
                    delta = choice.delta
                    content_piece = _extract_text(getattr(delta, "content", None))
                    if content_piece:
                        yield content_piece
        except Exception as exc:
            logger.error("OpenAI streaming API error: %s", exc)
            raise ExternalServiceError("OpenAI", exc)
