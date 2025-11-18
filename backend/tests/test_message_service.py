import pytest
from unittest.mock import AsyncMock, patch
from app.services.message_service import MessageService
from app.models.message import Message
from app.models.chat import Chat
from app.models.agent import Agent

@pytest.mark.asyncio
class TestMessageService:
    """Tests pour le service de gestion des messages"""
    
    async def test_create_message(self, db_session, test_chat_id):
        """Test de création d'un message"""
        message_service = MessageService(db_session)
        
        message = await message_service.create_message(
            chat_id=str(test_chat_id),
            role="user",
            content="Message de test",
            model_used="test-model",
            tokens_used=50,
            processing_time=1.2,
            temperature=0.7
        )
        
        assert message.id is not None
        assert message.chat_id == test_chat_id
        assert message.role == "user"
        assert message.content == "Message de test"
        assert message.model_used == "test-model"
        assert message.tokens_used == 50
        assert message.processing_time == 1.2
        assert message.temperature == 0.7
    
    async def test_get_chat_history(self, db_session, test_chat_id):
        """Test de récupération de l'historique des messages"""
        message_service = MessageService(db_session)
        
        # Créer quelques messages
        await message_service.create_message(
            str(test_chat_id), "user", "Premier message"
        )
        await message_service.create_message(
            str(test_chat_id), "assistant", "Réponse de l'assistant"
        )
        
        # Récupérer l'historique
        history = await message_service.get_chat_history(str(test_chat_id))
        
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Premier message"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Réponse de l'assistant"
    
    async def test_validate_chat_user(self, db_session, test_user_id, test_chat_id):
        """Test de validation de propriété d'un chat"""
        # Créer un chat
        chat = Chat(
            id=test_chat_id,
            title="Chat de test",
            user_id=test_user_id,
            is_active=True
        )
        db_session.add(chat)
        await db_session.commit()
        
        message_service = MessageService(db_session)
        
        # Test avec le bon utilisateur
        is_valid = await message_service.validate_chat_user(
            str(test_chat_id), test_user_id
        )
        assert is_valid is True
        
        # Test avec un mauvais utilisateur
        from uuid import uuid4
        wrong_user_id = uuid4()
        is_valid = await message_service.validate_chat_user(
            str(test_chat_id), wrong_user_id
        )
        assert is_valid is False
    
    @patch('app.services.message_service.MessageService.mistral')
    async def test_generate_ai_response(self, mock_mistral, db_session, test_user_id, test_chat_id, test_agent_id):
        """Test de génération de réponse IA"""
        # Créer un agent
        agent = Agent(
            id=test_agent_id,
            name="Test Agent",
            system_prompt="Tu es un assistant de test.",
            category="test",
            user_id=test_user_id,
            is_active=True,
            tags=["test"]
        )
        db_session.add(agent)
        
        # Créer un chat
        chat = Chat(
            id=test_chat_id,
            title="Chat de test",
            user_id=test_user_id,
            agent_id=test_agent_id,
            is_active=True
        )
        db_session.add(chat)
        await db_session.commit()
        
        # Mock de la réponse Mistral
        mock_mistral.generate_response_with_metadata = AsyncMock(
            return_value=("Réponse de test", {"tokens_used": 25, "processing_time": 0.5})
        )
        
        message_service = MessageService(db_session)
        
        messages = [{"role": "user", "content": "Test message"}]
        response, metadata = await message_service.generate_ai_response(
            messages, chat_id=str(test_chat_id)
        )
        
        assert response == "Réponse de test"
        assert metadata["tokens_used"] == 25
        assert metadata["agent_id"] == str(test_agent_id)
        assert metadata["agent_name"] == "Test Agent"
    
    async def test_get_agent_documents_content_no_documents(self, db_session, test_agent_id):
        """Test de récupération de contenu de documents sans documents"""
        message_service = MessageService(db_session)
        
        content = await message_service.get_agent_documents_content(test_agent_id)
        
        assert content == ""