import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# S'assurer que le mode API et la configuration minimale sont définis pour ces tests
os.environ.setdefault("LLM_MODE", "api")
os.environ.setdefault("API_URL", os.environ.get("API_URL", "https://api.mistral.ai/v1/chat/completions"))
os.environ.setdefault("API_KEY", os.environ.get("API_KEY", "test-api-key"))

from app.services.mistral_service import MistralService
from app.utils.exceptions import ExternalServiceError

@pytest.mark.asyncio
class TestMistralService:
    """Tests pour le service Mistral"""
    
    @patch('app.services.mistral_service.httpx.AsyncClient')
    async def test_generate_response_success(self, mock_async_client_class):
        """Test de génération de réponse réussie"""
        # Mock du client HTTP
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Réponse de test",
                    }
                }
            ]
        }
        mock_client.post.return_value = mock_response
        mock_async_client_class.return_value = mock_client

        mistral_service = MistralService()
        messages = [{"role": "user", "content": "Test"}]

        response = await mistral_service.generate_response(messages)

        assert response == "Réponse de test"
        mock_client.post.assert_awaited_once()
    
    @patch('app.services.mistral_service.httpx.AsyncClient')
    async def test_generate_response_with_metadata(self, mock_async_client_class):
        """Test de génération de réponse avec métadonnées"""
        # Mock du client HTTP avec usage
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Réponse avec métadonnées",
                    }
                }
            ],
            "usage": {
                "total_tokens": 100,
                "prompt_tokens": 40,
                "completion_tokens": 60,
            },
        }

        mock_client.post.return_value = mock_response
        mock_async_client_class.return_value = mock_client

        mistral_service = MistralService()
        messages = [{"role": "user", "content": "Test avec métadonnées"}]

        response, metadata = await mistral_service.generate_response_with_metadata(messages)

        assert response == "Réponse avec métadonnées"
        assert metadata["tokens_used"] == 100
        assert metadata["prompt_tokens"] == 40
        assert metadata["completion_tokens"] == 60
        assert "processing_time" in metadata
        assert metadata["temperature"] == 0.7
    
    @patch('app.services.mistral_service.httpx.AsyncClient')
    async def test_generate_response_error(self, mock_async_client_class):
        """Test de gestion d'erreur lors de la génération"""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal error"
        mock_client.post.return_value = mock_response
        mock_async_client_class.return_value = mock_client

        mistral_service = MistralService()
        messages = [{"role": "user", "content": "Test erreur"}]

        with pytest.raises(ExternalServiceError) as exc_info:
            await mistral_service.generate_response(messages)

        assert "LLM API" in str(exc_info.value)
    
    @patch('app.services.mistral_service.httpx.AsyncClient')
    async def test_generate_stream_response(self, mock_async_client_class):
        """Test de génération de réponse en streaming"""
        # Mock du client pour le streaming SSE
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client

        mock_stream_ctx = AsyncMock()
        mock_stream_ctx.__aenter__.return_value = mock_stream_ctx
        mock_stream_ctx.status_code = 200

        async def fake_aiter_lines():
            yield 'data: {"choices":[{"delta":{"content":"Partie 1"}}]}'
            yield 'data: {"choices":[{"delta":{"content":"Partie 2"}}]}'
            yield "data: [DONE]"

        mock_stream_ctx.aiter_lines.return_value = fake_aiter_lines()
        mock_client.stream.return_value = mock_stream_ctx
        mock_async_client_class.return_value = mock_client

        mistral_service = MistralService()
        messages = [{"role": "user", "content": "Test streaming"}]

        chunks = []
        async for chunk in mistral_service.generate_stream_response(messages):
            chunks.append(chunk)

        assert chunks == ["Partie 1", "Partie 2"]
    
    @patch('app.services.mistral_service.httpx.AsyncClient')
    async def test_generate_stream_response_error(self, mock_async_client_class):
        """Test de gestion d'erreur lors du streaming"""
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client

        mock_stream_ctx = AsyncMock()
        mock_stream_ctx.__aenter__.return_value = mock_stream_ctx
        mock_stream_ctx.status_code = 500
        mock_stream_ctx.text = "Erreur streaming"

        async def fake_aiter_lines():
            if False:
                yield ""

        mock_stream_ctx.aiter_lines.return_value = fake_aiter_lines()
        mock_client.stream.return_value = mock_stream_ctx
        mock_async_client_class.return_value = mock_client

        mistral_service = MistralService()
        messages = [{"role": "user", "content": "Test erreur streaming"}]

        with pytest.raises(ExternalServiceError):
            async for _ in mistral_service.generate_stream_response(messages):
                pass
