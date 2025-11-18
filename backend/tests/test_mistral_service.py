import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.mistral_service import MistralService
from app.utils.exceptions import ExternalServiceError

@pytest.mark.asyncio
class TestMistralService:
    """Tests pour le service Mistral"""
    
    @patch('app.services.mistral_service.Mistral')
    async def test_generate_response_success(self, mock_mistral_class):
        """Test de génération de réponse réussie"""
        # Mock du client Mistral
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Réponse de test"
        
        mock_client.chat.complete.return_value = mock_response
        mock_mistral_class.return_value = mock_client
        
        # Mock de asyncio.to_thread pour simuler l'appel asynchrone
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            
            mistral_service = MistralService()
            messages = [{"role": "user", "content": "Test"}]
            
            response = await mistral_service.generate_response(messages)
            
            assert response == "Réponse de test"
            mock_to_thread.assert_called_once()
    
    @patch('app.services.mistral_service.Mistral')
    async def test_generate_response_with_metadata(self, mock_mistral_class):
        """Test de génération de réponse avec métadonnées"""
        # Mock du client Mistral avec usage
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Réponse avec métadonnées"
        mock_response.usage.total_tokens = 100
        
        mock_client.chat.complete.return_value = mock_response
        mock_mistral_class.return_value = mock_client
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            
            mistral_service = MistralService()
            messages = [{"role": "user", "content": "Test avec métadonnées"}]
            
            response, metadata = await mistral_service.generate_response_with_metadata(messages)
            
            assert response == "Réponse avec métadonnées"
            assert metadata["tokens_used"] == 100
            assert "processing_time" in metadata
            assert metadata["temperature"] == 0.7
    
    @patch('app.services.mistral_service.Mistral')
    async def test_generate_response_error(self, mock_mistral_class):
        """Test de gestion d'erreur lors de la génération"""
        mock_client = MagicMock()
        mock_client.chat.complete.side_effect = Exception("Erreur API")
        mock_mistral_class.return_value = mock_client
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = Exception("Erreur API")
            
            mistral_service = MistralService()
            messages = [{"role": "user", "content": "Test erreur"}]
            
            with pytest.raises(ExternalServiceError) as exc_info:
                await mistral_service.generate_response(messages)
            
            assert "Mistral AI" in str(exc_info.value)
    
    @patch('app.services.mistral_service.Mistral')
    async def test_generate_stream_response(self, mock_mistral_class):
        """Test de génération de réponse en streaming"""
        # Mock du client pour le streaming
        mock_client = MagicMock()
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Partie 1"
        
        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = "Partie 2"
        
        mock_stream = [mock_chunk1, mock_chunk2]
        mock_client.chat.stream.return_value = mock_stream
        mock_mistral_class.return_value = mock_client
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_stream
            
            mistral_service = MistralService()
            messages = [{"role": "user", "content": "Test streaming"}]
            
            chunks = []
            async for chunk in mistral_service.generate_stream_response(messages):
                chunks.append(chunk)
            
            assert chunks == ["Partie 1", "Partie 2"]
    
    @patch('app.services.mistral_service.Mistral')
    async def test_generate_stream_response_error(self, mock_mistral_class):
        """Test de gestion d'erreur lors du streaming"""
        mock_client = MagicMock()
        mock_client.chat.stream.side_effect = Exception("Erreur streaming")
        mock_mistral_class.return_value = mock_client
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = Exception("Erreur streaming")
            
            mistral_service = MistralService()
            messages = [{"role": "user", "content": "Test erreur streaming"}]
            
            with pytest.raises(ExternalServiceError):
                async for chunk in mistral_service.generate_stream_response(messages):
                    pass