import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.openai_service import OpenAIService
from app.utils.exceptions import ExternalServiceError


class _AsyncIterator:
    def __init__(self, items):
        self._iter = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


@pytest.mark.asyncio
async def test_generate_response_success():
    with patch("app.services.openai_service.AsyncOpenAI") as mock_client_cls:
        mock_client = MagicMock()
        message = MagicMock(content="Réponse de test", tool_calls=[])
        response = MagicMock()
        response.choices = [MagicMock(message=message)]
        mock_client.chat.completions.create = AsyncMock(return_value=response)
        mock_client_cls.return_value = mock_client

        service = OpenAIService()
        result = await service.generate_response([{"role": "user", "content": "Test"}])

        assert result == "Réponse de test"
        mock_client.chat.completions.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_response_with_metadata():
    with patch("app.services.openai_service.AsyncOpenAI") as mock_client_cls:
        mock_client = MagicMock()
        message = MagicMock(content="Réponse avec métadonnées", tool_calls=[])
        response = MagicMock()
        response.choices = [MagicMock(message=message)]
        usage = MagicMock(total_tokens=42, prompt_tokens=21, completion_tokens=21)
        response.usage = usage
        mock_client.chat.completions.create = AsyncMock(return_value=response)
        mock_client_cls.return_value = mock_client

        service = OpenAIService()
        content, metadata = await service.generate_response_with_metadata(
            [{"role": "user", "content": "Hello"}]
        )

        assert content == "Réponse avec métadonnées"
        assert metadata["tokens_used"] == 42
        assert metadata["prompt_tokens"] == 21
        assert metadata["completion_tokens"] == 21


@pytest.mark.asyncio
async def test_generate_response_error():
    with patch("app.services.openai_service.AsyncOpenAI") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Erreur API"))
        mock_client_cls.return_value = mock_client

        service = OpenAIService()
        with pytest.raises(ExternalServiceError):
            await service.generate_response([{"role": "user", "content": "Test"}])


@pytest.mark.asyncio
async def test_generate_stream_response():
    with patch("app.services.openai_service.AsyncOpenAI") as mock_client_cls:
        mock_client = MagicMock()
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock(delta=MagicMock(content="Partie 1"))]
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock(delta=MagicMock(content="Partie 2"))]
        mock_client.chat.completions.create = AsyncMock(return_value=_AsyncIterator([chunk1, chunk2]))
        mock_client_cls.return_value = mock_client

        service = OpenAIService()
        chunks = []
        async for piece in service.generate_stream_response([{"role": "user", "content": "Hello"}]):
            chunks.append(piece)

        assert chunks == ["Partie 1", "Partie 2"]
