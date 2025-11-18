from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload
from app.models.message import Message
from app.models.chat import Chat
from app.models.agent import Agent
from app.models.document import Document, EntityType
from app.models.document_chunk import DocumentChunk
from app.services.llm_service import get_llm_service
from app.services.document_service import document_service
from app.services.embedding_service import embedding_service
from app.utils.cache import cache_service
from app.config import settings
from typing import List, Dict, Optional
import uuid
import hashlib
from pathlib import Path
import aiofiles
import math
import logging

FORCE_POWERPOINT_MARKER = "force_powerpoint_tool"
POWERPOINT_FUNCTION_NAME = "generate_powerpoint_from_text"


def _should_force_powerpoint(agent: Optional[Agent]) -> bool:
    """Returns True when the agent must expose the PowerPoint tool systematically."""
    if not agent:
        return False

    markers = {FORCE_POWERPOINT_MARKER}
    try:
        tags = {tag.lower() for tag in (agent.tags or [])}
    except TypeError:
        tags = set()
    try:
        capabilities = {cap.lower() for cap in (agent.capabilities or [])}
    except TypeError:
        capabilities = set()

    return bool(markers & tags) or bool(markers & capabilities)

class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_service()
    
    async def create_message(
        self, 
        chat_id: str, 
        role: str, 
        content: str,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None,
        processing_time: Optional[float] = None,
        temperature: Optional[float] = None
    ) -> Message:
        message = Message(
            chat_id=uuid.UUID(chat_id),
            role=role,
            content=content,
            model_used=model_used,
            tokens_used=tokens_used,
            processing_time=processing_time,
            temperature=temperature
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_message_with_chat(self, message_id: str) -> Optional[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.id == uuid.UUID(message_id))
            .options(selectinload(Message.chat))
        )
        return result.scalar_one_or_none()

    async def update_user_message_content(self, message: Message, content: str) -> Message:
        message.content = content
        message.is_edited = True
        await self.db.commit()
        await self.db.refresh(message)
        return message
    
    async def get_chat_history(self, chat_id: str) -> List[Dict]:
        # R�cup�rer les 20 derniers messages
        result = await self.db.execute(
            select(Message)
            .where(Message.chat_id == uuid.UUID(chat_id))
            .order_by(Message.created_at.desc())
            .limit(20)
        )
        messages = result.scalars().all()
        
        # Convertir au format Mistral
        return [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(messages)
        ]
    
    async def get_chat_agent(self, chat_id: str) -> Optional[Agent]:
        # R�cup�rer l'agent associ� au chat avec eager loading
        result = await self.db.execute(
            select(Chat)
            .where(Chat.id == uuid.UUID(chat_id))
            .options(selectinload(Chat.agent))
        )
        chat = result.scalar_one_or_none()
        
        if chat and chat.agent:
            return chat.agent
        return None
    
    async def validate_chat_session(self, chat_id: str, session_id: str) -> bool:
        # V�rifier que le chat appartient bien � la session
        result = await self.db.execute(
            select(Chat)
            .where(Chat.id == uuid.UUID(chat_id))
            .where(Chat.session_id == uuid.UUID(session_id))
        )
        return result.scalar_one_or_none() is not None
    
    async def validate_chat_user(self, chat_id: str, user_id: uuid.UUID) -> bool:
        # V�rifier que le chat appartient bien � l'utilisateur
        result = await self.db.execute(
            select(Chat)
            .where(Chat.id == uuid.UUID(chat_id))
            .where(Chat.user_id == user_id)
        )
        return result.scalar_one_or_none() is not None
    
    async def delete_last_assistant_message(self, chat_id: str) -> bool:
        """Supprime le dernier message assistant d'un chat pour régénération"""
        # Récupérer le dernier message assistant
        result = await self.db.execute(
            select(Message)
            .where(
                and_(
                    Message.chat_id == uuid.UUID(chat_id),
                    Message.role == "assistant"
                )
            )
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_assistant_message = result.scalar_one_or_none()
        
        if last_assistant_message:
            await self.db.delete(last_assistant_message)
            await self.db.commit()
            return True
        return False
    
    async def get_agent_documents_content(self, agent_id: uuid.UUID) -> str:
        # Essayer de récupérer depuis le cache
        cache_key = cache_service.generate_key("agent_docs", str(agent_id))
        cached_content = await cache_service.get(cache_key)
        if cached_content:
            return cached_content
        
        result = await self.db.execute(
            select(Document)
            .where(
                and_(
                    Document.entity_type == EntityType.AGENT,
                    Document.entity_id == agent_id,
                    Document.processed_path.isnot(None)
                )
            )
        )
        documents = result.scalars().all()
        
        if not documents:
            return ""
        
        document_contents = []
        storage_path = Path(settings.storage_path)
        
        for doc in documents:
            if doc.processed_path:
                processed_file = storage_path / doc.processed_path
                if processed_file.exists():
                    async with aiofiles.open(processed_file, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        if content:
                            document_contents.append(f"### Document: {doc.name}\n{content}\n")
        
        if document_contents:
            final_content = "\n## Documents de référence:\n" + "\n".join(document_contents)
        else:
            final_content = ""
        
        # Mettre en cache pour 1 heure
        await cache_service.set(cache_key, final_content, expire_seconds=3600)
        return final_content
    
    async def get_chat_documents_content(self, chat_id: uuid.UUID) -> str:
        """Récupère le contenu des documents d'un chat avec cache"""
        # Essayer de récupérer depuis le cache
        cache_key = cache_service.generate_key("chat_docs", str(chat_id))
        cached_content = await cache_service.get(cache_key)
        if cached_content:
            return cached_content
        
        # Récupérer les documents du chat
        result = await self.db.execute(
            select(Document)
            .where(
                and_(
                    Document.entity_type == EntityType.CHAT,
                    Document.entity_id == chat_id,
                    Document.processed_path.isnot(None)
                )
            )
        )
        documents = result.scalars().all()
        
        if not documents:
            return ""
        
        document_contents = []
        storage_path = Path(settings.storage_path)
        
        for doc in documents:
            if doc.processed_path:
                processed_file = storage_path / doc.processed_path
                if processed_file.exists():
                    async with aiofiles.open(processed_file, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        if content:
                            document_contents.append(f"### Document: {doc.name}\n{content}\n")
        
        if document_contents:
            final_content = "\n## Documents joints:\n" + "\n".join(document_contents)
        else:
            final_content = ""
        
        # Mettre en cache pour 30 minutes (plus court car les docs de chat peuvent changer plus souvent)
        await cache_service.set(cache_key, final_content, expire_seconds=1800)
        return final_content

    def _extract_latest_user_question(self, messages: List[Dict]) -> Optional[str]:
        """Récupère le dernier message utilisateur non vide"""
        for msg in reversed(messages):
            if msg.get("role") == "user" and msg.get("content") and msg["content"].strip():
                return msg["content"].strip()
        return None

    async def _build_rag_context(self, chat: Chat, query: str, top_k: int = 6) -> tuple[str, List[dict]]:
        """Recherche les chunks pertinents et construit un contexte formaté.
        Retourne le texte et la liste des hits (pour affichage UI).
        """
        try:
            query_vector = await embedding_service.embed_query(query)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to embed query for RAG context: {e}")
            return "", []

        if not query_vector:
            return "", []

        hits: List[tuple[float, DocumentChunk, Document]] = []

        await document_service._ensure_enums_normalized(self.db)

        async def collect_for_entity(entity_type: EntityType, entity_id: uuid.UUID):
            result = await self.db.execute(
                select(DocumentChunk, Document)
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(Document.entity_type == entity_type)
                .where(Document.entity_id == entity_id)
            )
            rows = result.all()
            for dc, doc in rows:
                vec = dc.embedding or []
                if not vec:
                    continue
                score = self._cosine_similarity(query_vector, vec)
                if score <= 0:
                    continue
                hits.append((float(score), dc, doc))

        await collect_for_entity(EntityType.CHAT, chat.id)
        if chat.agent_id:
            await collect_for_entity(EntityType.AGENT, chat.agent_id)

        if not hits:
            return "", []

        hits.sort(key=lambda item: item[0], reverse=True)
        context_lines: List[str] = []
        ui_hits: List[dict] = []
        for idx, (score, chunk, document) in enumerate(hits[:top_k], start=1):
            title = document.name or "Document"
            context_lines.append(f"[{idx}] {title} — score {score:.3f}")
            context_lines.append(chunk.content.strip())
            context_lines.append("")
            ui_hits.append(
                {
                    "chunk_id": str(chunk.id),
                    "document_id": str(document.id),
                    "document_name": title,
                    "score": float(score),
                    "content": chunk.content,
                }
            )

        return "\n".join(context_lines).strip(), ui_hits

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        if not a or not b:
            return 0.0
        size = min(len(a), len(b))
        dot = sum(a[i] * b[i] for i in range(size))
        norm_a = math.sqrt(sum(x * x for x in a[:size]))
        norm_b = math.sqrt(sum(x * x for x in b[:size]))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    
    async def generate_ai_response(
        self, 
        messages: List[Dict], 
        system_prompt: Optional[str] = None,
        chat_id: Optional[str] = None
    ) -> tuple[str, Dict]:
        # Générer une clé de cache basée sur les messages et le contexte
        messages_hash = hashlib.md5(str(messages).encode()).hexdigest()
        cache_key = cache_service.generate_key("ai_response", chat_id or "no_chat", messages_hash)
        
        # Essayer de récupérer la réponse depuis le cache
        cached_response = await cache_service.get(cache_key)
        if cached_response and isinstance(cached_response, dict):
            return cached_response.get("response", ""), cached_response.get("metadata", {})
        
        # Construire le prompt système enrichi
        enhanced_system_prompt = system_prompt or "Tu es un assistant utile."
        agent = None
        agent_info: Dict[str, Optional[str]] = {}
        chat = None
        
        # Si on a un chat_id, récupérer toutes les données en une seule requête
        if chat_id:
            # Récupérer le chat avec l'agent et tous les documents en une requête
            chat_result = await self.db.execute(
                select(Chat)
                .where(Chat.id == uuid.UUID(chat_id))
                .options(selectinload(Chat.agent))
            )
            chat = chat_result.scalar_one_or_none()
            
            if chat and chat.agent:
                agent = chat.agent
                # Snapshot des infos agent pour éviter tout lazy-load plus tard
                try:
                    agent_info = {
                        "id": str(agent.id) if getattr(agent, "id", None) is not None else None,
                        "name": getattr(agent, "name", None),
                        "model": getattr(agent, "model", None),
                    }
                except Exception:
                    agent_info = {}
                # Ne pas écraser un system_prompt fourni (peut contenir le RAG context)
                if not system_prompt:
                    enhanced_system_prompt = agent.system_prompt
                
                # En mode RAG-only, ne pas injecter les contenus bruts
                if not settings.rag_only:
                    # Récupérer tous les documents (agent et chat) en parallèle
                    if agent.id:
                        agent_docs_content = await self.get_agent_documents_content(agent.id)
                        if agent_docs_content:
                            enhanced_system_prompt += "\n" + agent_docs_content
            
            # Ajouter les documents du chat (désactivé en mode RAG-only)
            if not settings.rag_only:
                chat_docs_content = await self.get_chat_documents_content(uuid.UUID(chat_id))
                if chat_docs_content:
                    enhanced_system_prompt += "\n" + chat_docs_content

            # Construire un contexte RAG basé sur la dernière question utilisateur
            rag_hits: List[dict] = []
            if chat:
                user_query = self._extract_latest_user_question(messages)
                if user_query:
                    rag_context, rag_hits = await self._build_rag_context(chat, user_query)
                    if rag_context:
                        enhanced_system_prompt += "\n\n=== Contexte RAG ===\n" + rag_context
        
        force_powerpoint = _should_force_powerpoint(agent)

        # Outils MCP: activer sur demande explicite ou si l'agent est consacré au PowerPoint
        from app.services.mcp_service import get_mcp_service
        import logging
        logger = logging.getLogger(__name__)

        def _is_powerpoint_request(msgs: List[Dict]) -> bool:
            if force_powerpoint:
                return True

            # Détection robuste des requêtes PowerPoint
            strict = [
                "powerpoint", "power point", "ppt", "pptx",
                "slide deck", "slide-deck", "slide", "slides",
                "diapo", "diapos", "diapositive", "diapositives",
                "diaporama", "deck"
            ]
            soft = ["présentation", "presentations", "presentation", "présentations"]
            amplifiers = ["power", "ppt", "pptx", "slide", "slides", "diapo", "deck", "diaporama"]
            for m in reversed(msgs):
                if m.get("role") == "user" and m.get("content"):
                    text = m["content"].lower()
                    if any(k in text for k in strict):
                        return True
                    if any(s in text for s in soft) and any(a in text for a in amplifiers):
                        return True
            return False

        mcp_service = get_mcp_service()
        tools = []
        try:
            if _is_powerpoint_request(messages):
                available = await mcp_service.get_available_tools()
                # Ne proposer que l'outil PowerPoint
                tools = [t for t in available if t.get("function", {}).get("name") == "generate_powerpoint_from_text"]
                if tools:
                    logger.info("MCP tools enabled for this prompt: PowerPoint")
                    if force_powerpoint:
                        enhanced_system_prompt += (
                            "\n\nTu es un générateur officiel de présentations. Utilise systématiquement l'outil "
                            "de génération PowerPoint pour produire une sortie en PPTX, en évitant de rédiger "
                            "toi-même la présentation finale."
                        )
                    else:
                        enhanced_system_prompt += (
                            "\n\nSi et seulement si l'utilisateur demande explicitement une présentation, tu peux utiliser "
                            "l'outil de génération PowerPoint."
                        )
                elif force_powerpoint:
                    logger.warning("PowerPoint tool expected but not available")
            else:
                logger.info("No MCP tools enabled for this prompt")
        except Exception as e:
            logger.error(f"Failed to prepare MCP tools: {e}")
            tools = []
        
        # Limiter la taille du system prompt pour éviter les débordements (docs très volumineux)
        MAX_SYSTEM_CHARS = 60000
        if len(enhanced_system_prompt) > MAX_SYSTEM_CHARS:
            enhanced_system_prompt = enhanced_system_prompt[:MAX_SYSTEM_CHARS] + "\n\n[Contexte tronqué pour rester dans la limite]"

        # Ajouter le system prompt enrichi et filtrer les messages vides
        final_messages = [{"role": "system", "content": enhanced_system_prompt}]
        
        # Filtrer les messages vides et limiter la taille pour éviter l'erreur Mistral
        total_chars = len(enhanced_system_prompt)
        MAX_CHARS = 300000  # Environ 75k tokens (4 chars ≈ 1 token)
        
        at_least_one_user_added = False
        for msg in messages:
            if msg.get("content") and msg["content"].strip():
                content = msg["content"]
                # Si on dépasse la limite, tronquer le message
                if total_chars + len(content) > MAX_CHARS:
                    remaining = MAX_CHARS - total_chars
                    if remaining > 1000:  # Au moins 1000 caractères
                        content = content[:remaining] + "\n\n[Message tronqué car trop long]"
                        logger.warning(f"Truncating message from {len(msg['content'])} to {remaining} chars")
                        final_messages.append({"role": msg["role"], "content": content})
                        if msg["role"] == "user":
                            at_least_one_user_added = True
                        break  # Arrêter d'ajouter des messages
                    else:
                        logger.warning(f"Skipping message, context limit reached")
                        # Si aucun message utilisateur n'a été ajouté, forcer l'ajout du dernier user
                        if not at_least_one_user_added:
                            # Trouver le dernier message utilisateur
                            last_user = None
                            for m in reversed(messages):
                                if m.get("role") == "user" and m.get("content"):
                                    last_user = m
                                    break
                            if last_user:
                                forced = last_user["content"][:2000] + "\n\n[Message réduit car le contexte est trop volumineux]"
                                final_messages.append({"role": "user", "content": forced})
                                at_least_one_user_added = True
                        break
                final_messages.append(msg)
                total_chars += len(content)
                if msg["role"] == "user":
                    at_least_one_user_added = True
            else:
                logger.warning(f"Skipping empty message with role: {msg.get('role')}")
        
        # S'assurer qu'il y a au moins un message utilisateur
        if len(final_messages) == 1:  # Seulement le system message
            logger.error("No valid messages to send to Mistral")
            return "Désolé, je n'ai pas pu traiter votre demande. Veuillez réessayer.", {}
        
        # Appeler Mistral avec métadonnées et outils
        # Déterminer la température effective: si des documents RAG sont disponibles pour ce chat, forcer à 0.0
        effective_temperature: float | None = None
        try:
            if chat_id:
                from app.models.document import Document, ProcessingStatus, EntityType
                result = await self.db.execute(
                    select(Document)
                    .where(
                        and_(
                            Document.entity_type == EntityType.CHAT,
                            Document.entity_id == uuid.UUID(chat_id),
                            Document.processing_status == ProcessingStatus.COMPLETED,
                        )
                    )
                    .limit(1)
                )
                has_docs = result.first() is not None
                if has_docs:
                    effective_temperature = 0.0
        except Exception:
            # Si la requête échoue, rollback pour ne pas bloquer l'insertion du message assistant
            try:
                await self.db.rollback()
            except Exception:
                pass

        response, metadata = await self.llm.generate_response_with_metadata(
            final_messages,
            tools,
            temperature=effective_temperature,
            tool_choice=POWERPOINT_FUNCTION_NAME if force_powerpoint else None,
        )

        if chat_id and locals().get("rag_hits"):
            metadata["rag_hits"] = locals()["rag_hits"]
        
        # Enrichir les métadonnées avec les informations de l'agent
        try:
            if agent_info:
                if agent_info.get("id"):
                    metadata["agent_id"] = agent_info["id"]
                if agent_info.get("name"):
                    metadata["agent_name"] = agent_info["name"]
                if agent_info.get("model"):
                    metadata["agent_model"] = agent_info["model"]
        except Exception:
            pass
        
        # Mettre en cache la réponse pour 10 minutes
        cache_data = {"response": response, "metadata": metadata}
        await cache_service.set(cache_key, cache_data, expire_seconds=600)
        
        return response, metadata
    
    async def generate_ai_stream_response(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        chat_id: Optional[str] = None
    ):
        """Génère une réponse en streaming en alignant le contexte avec la version non-streaming."""
        enhanced_system_prompt = system_prompt or "Tu es un assistant utile."
        agent: Optional[Agent] = None
        agent_info: Dict[str, Optional[str]] = {}

        # Si on a un chat_id, récupérer le chat, l'agent et préparer le contexte documentaire
        chat: Optional[Chat] = None
        if chat_id:
            chat_result = await self.db.execute(
                select(Chat)
                .where(Chat.id == uuid.UUID(chat_id))
                .options(selectinload(Chat.agent))
            )
            chat = chat_result.scalar_one_or_none()

            if chat and chat.agent:
                agent = chat.agent
                try:
                    agent_info = {
                        "id": str(agent.id) if getattr(agent, "id", None) is not None else None,
                        "name": getattr(agent, "name", None),
                        "model": getattr(agent, "model", None),
                    }
                except Exception:
                    agent_info = {}

                if not system_prompt:
                    enhanced_system_prompt = agent.system_prompt

                if not settings.rag_only and agent.id:
                    agent_docs_content = await self.get_agent_documents_content(agent.id)
                    if agent_docs_content:
                        enhanced_system_prompt += "\n" + agent_docs_content

            if chat and not settings.rag_only:
                chat_docs_content = await self.get_chat_documents_content(uuid.UUID(chat_id))
                if chat_docs_content:
                    enhanced_system_prompt += "\n" + chat_docs_content

            if chat:
                try:
                    user_query = self._extract_latest_user_question(messages)
                    if user_query:
                        rag_context, _rag_hits = await self._build_rag_context(chat, user_query)
                        if rag_context:
                            enhanced_system_prompt += "\n\n=== Contexte RAG ===\n" + rag_context
                except Exception as exc:
                    logger = logging.getLogger(__name__)
                    logger.error("RAG context build failed during streaming: %s", exc, exc_info=True)

        force_powerpoint = _should_force_powerpoint(agent)

        # Outils MCP: n'activer que sur demande explicite ou pour les agents officiels PowerPoint
        from app.services.mcp_service import get_mcp_service
        import logging
        logger = logging.getLogger(__name__)
        
        def _is_powerpoint_request(msgs: List[Dict]) -> bool:
            if force_powerpoint:
                return True

            strict = [
                "powerpoint", "power point", "ppt", "pptx",
                "slide deck", "slide-deck", "slide", "slides",
                "diapo", "diapos", "diapositive", "diapositives",
                "diaporama", "deck"
            ]
            soft = ["présentation", "presentations", "presentation", "présentations"]
            amplifiers = ["power", "ppt", "pptx", "slide", "slides", "diapo", "deck", "diaporama"]
            for m in reversed(msgs):
                if m.get("role") == "user" and m.get("content"):
                    text = m["content"].lower()
                    if any(k in text for k in strict):
                        return True
                    if any(s in text for s in soft) and any(a in text for a in amplifiers):
                        return True
            return False
        
        mcp_service = get_mcp_service()
        tools = []
        try:
            if _is_powerpoint_request(messages):
                available = await mcp_service.get_available_tools()
                tools = [t for t in available if t.get("function", {}).get("name") == "generate_powerpoint_from_text"]
                if tools:
                    logger.info("MCP tools enabled for this prompt: PowerPoint")
                    if force_powerpoint:
                        enhanced_system_prompt += (
                            "\n\nTu es un générateur officiel de présentations. Utilise systématiquement l'outil "
                            "de génération PowerPoint pour produire une sortie en PPTX, en évitant de rédiger "
                            "toi-même la présentation finale."
                        )
                    else:
                        enhanced_system_prompt += (
                            "\n\nSi et seulement si l'utilisateur demande explicitement une présentation, tu peux utiliser "
                            "l'outil de génération PowerPoint."
                        )
                elif force_powerpoint:
                    logger.warning("PowerPoint tool expected but not available")
            else:
                logger.info("No MCP tools enabled for this prompt")
        except Exception as e:
            logger.error(f"Failed to prepare MCP tools: {e}")
            tools = []
        
        # Limiter la taille du system prompt pour le streaming également
        MAX_SYSTEM_CHARS = 60000
        if len(enhanced_system_prompt) > MAX_SYSTEM_CHARS:
            enhanced_system_prompt = enhanced_system_prompt[:MAX_SYSTEM_CHARS] + "\n\n[Contexte tronqué pour rester dans la limite]"

        # Filtrer les messages vides et tronquer si nécessaire pour éviter les débordements
        total_chars = len(enhanced_system_prompt)
        MAX_CHARS = 300000
        at_least_one_user_added = False
        filtered_messages: List[Dict] = []

        for msg in messages:
            content = msg.get("content")
            if not content or not content.strip():
                continue

            if total_chars + len(content) > MAX_CHARS:
                remaining = MAX_CHARS - total_chars
                if remaining > 1000:
                    truncated = content[:remaining] + "\n\n[Message tronqué car trop long]"
                    filtered_messages.append({"role": msg["role"], "content": truncated})
                    if msg["role"] == "user":
                        at_least_one_user_added = True
                else:
                    if not at_least_one_user_added and msg["role"] == "user":
                        forced = content[:2000] + "\n\n[Message réduit car le contexte est trop volumineux]"
                        filtered_messages.append({"role": "user", "content": forced})
                        at_least_one_user_added = True
                break

            filtered_messages.append(msg)
            total_chars += len(content)
            if msg["role"] == "user":
                at_least_one_user_added = True

        if not filtered_messages:
            logger = logging.getLogger(__name__)
            logger.error("No valid messages to stream after filtering")
            return

        final_messages = [{"role": "system", "content": enhanced_system_prompt}] + filtered_messages

        # Stream depuis Mistral avec outils
        # Déterminer la température effective aussi pour le streaming
        effective_temperature: float | None = None
        try:
            if chat_id:
                from app.models.document import Document, ProcessingStatus, EntityType
                result = await self.db.execute(
                    select(Document)
                    .where(
                        and_(
                            Document.entity_type == EntityType.CHAT,
                            Document.entity_id == uuid.UUID(chat_id),
                            Document.processing_status == ProcessingStatus.COMPLETED,
                        )
                    )
                    .limit(1)
                )
                has_docs = result.first() is not None
                if has_docs:
                    effective_temperature = 0.0
        except Exception:
            try:
                await self.db.rollback()
            except Exception:
                pass

        async for chunk in self.llm.generate_stream_response(
            final_messages,
            tools,
            temperature=effective_temperature,
            tool_choice=POWERPOINT_FUNCTION_NAME if force_powerpoint else None,
        ):
            yield chunk
