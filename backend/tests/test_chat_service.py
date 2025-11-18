import pytest
from uuid import UUID
from app.services.chat_service import ChatService
from app.models.chat import Chat
from app.models.agent import Agent
from app.schemas.chat import CreateChatRequest

@pytest.mark.asyncio
class TestChatService:
    """Tests pour le service de gestion des chats"""
    
    async def test_create_chat_with_agent(self, db_session, test_user_id, test_agent_id):
        """Test de création d'un chat avec un agent spécifique"""
        # Créer un agent de test
        agent = Agent(
            id=test_agent_id,
            name="Test Agent",
            description="Agent de test",
            system_prompt="Tu es un assistant de test.",
            category="test",
            user_id=test_user_id,
            is_public=False,
            is_active=True,
            tags=["test"]
        )
        db_session.add(agent)
        await db_session.commit()
        
        # Créer le service et le chat
        chat_service = ChatService(db_session)
        chat_data = CreateChatRequest(
            title="Chat de test",
            agent_id=test_agent_id
        )
        
        chat = await chat_service.create_chat(chat_data, test_user_id)
        
        assert chat.id is not None
        assert chat.title == "Chat de test"
        assert chat.agent_id == test_agent_id
        assert chat.user_id == test_user_id
        assert chat.is_active is True
    
    async def test_create_chat_without_agent(self, db_session, test_user_id):
        """Test de création d'un chat sans agent (utilise l'agent par défaut)"""
        chat_service = ChatService(db_session)
        chat_data = CreateChatRequest(title="Chat sans agent")
        
        chat = await chat_service.create_chat(chat_data, test_user_id)
        
        assert chat.id is not None
        assert chat.title == "Chat sans agent"
        assert chat.agent_id is not None  # Agent par défaut créé
        assert chat.user_id == test_user_id
    
    async def test_get_user_chats(self, db_session, test_user_id):
        """Test de récupération des chats d'un utilisateur"""
        chat_service = ChatService(db_session)
        
        # Créer quelques chats
        chat1_data = CreateChatRequest(title="Chat 1")
        chat2_data = CreateChatRequest(title="Chat 2")
        
        await chat_service.create_chat(chat1_data, test_user_id)
        await chat_service.create_chat(chat2_data, test_user_id)
        
        # Récupérer les chats
        chats = await chat_service.get_user_chats(test_user_id)
        
        assert len(chats) == 2
        assert all(chat.user_id == test_user_id for chat in chats)
        assert all(chat.is_active for chat in chats)
    
    async def test_update_chat_title(self, db_session, test_user_id):
        """Test de mise à jour du titre d'un chat"""
        chat_service = ChatService(db_session)
        
        # Créer un chat
        chat_data = CreateChatRequest(title="Titre original")
        chat = await chat_service.create_chat(chat_data, test_user_id)
        
        # Mettre à jour le titre
        updated_chat = await chat_service.update_chat_title(
            chat.id, "Nouveau titre", test_user_id
        )
        
        assert updated_chat.title == "Nouveau titre"
        assert updated_chat.id == chat.id
    
    async def test_delete_chat(self, db_session, test_user_id):
        """Test de suppression (désactivation) d'un chat"""
        chat_service = ChatService(db_session)
        
        # Créer un chat
        chat_data = CreateChatRequest(title="Chat à supprimer")
        chat = await chat_service.create_chat(chat_data, test_user_id)
        
        # Supprimer le chat
        await chat_service.delete_chat(chat.id, test_user_id)
        
        # Vérifier que le chat est désactivé
        from sqlalchemy import select
        result = await db_session.execute(
            select(Chat).where(Chat.id == chat.id)
        )
        updated_chat = result.scalar_one()
        assert updated_chat.is_active is False