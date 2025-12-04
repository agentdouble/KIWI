from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.schemas.message import (
    SendMessageRequest,
    MessageResponse,
    MessageFeedbackRequest,
    MessageFeedbackResponse,
    EditMessageRequest,
)
from app.services.message_service import MessageService
from app.services.feedback_service import FeedbackService
from app.utils.auth import get_current_active_user
from app.utils.rate_limit import limiter, AI_RATE_LIMIT
from app.utils.cache import cache_service
from app.services.rbac_service import (
    PERM_MESSAGE_SEND,
    PERM_MESSAGE_EDIT_OWN,
    PERM_MESSAGE_FEEDBACK,
    user_has_permission,
)
from app.models.user import User
from app.models.chat import Chat
from typing import Optional
import json
import logging

router = APIRouter()

@router.post("/debug")
async def debug_message(
    body: dict,
    request: Request,
    x_session_id: Optional[str] = Header(None)
):
    return {
        "received_body": body,
        "x_session_id_header": x_session_id,
        "headers_present": x_session_id is not None,
        "all_headers": dict(request.headers)
    }

@router.post("/test", response_model=MessageResponse)
async def test_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    x_session_id: Optional[str] = Header(None)
):
    if not x_session_id:
        raise HTTPException(status_code=400, detail="X-Session-ID header missing in test endpoint")
    
    service = MessageService(db)
    
    user_message = await service.create_message(
        chat_id=request.chat_id,
        role="user",
        content=request.content
    )
    
    assistant_message = await service.create_message(
        chat_id=request.chat_id,
        role="assistant",
        content="Test réussi ! J'ai reçu votre message."
    )
    
    return MessageResponse(
        id=str(assistant_message.id),
        role=assistant_message.role,
        content=assistant_message.content,
        created_at=assistant_message.created_at,
        chat_id=str(assistant_message.chat_id),
        user_message_id=str(user_message.id),
        is_edited=assistant_message.is_edited,
    )

@router.post("/", response_model=MessageResponse)
@limiter.limit(AI_RATE_LIMIT)
async def send_message(
    request: Request,
    message_request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    logger = logging.getLogger(__name__)
    lock_key = cache_service.generate_key("chat_lock", message_request.chat_id)
    lock_token: Optional[str] = None

    try:
        if not await user_has_permission(db, current_user, PERM_MESSAGE_SEND):
            raise HTTPException(status_code=403, detail="You are not allowed to send messages")
        lock_token = await cache_service.acquire_lock(lock_key, ttl_seconds=300)
        if lock_token is None:
            logger.warning("Concurrent send_message detected for chat %s", message_request.chat_id)
            raise HTTPException(
                status_code=409,
                detail="Une génération est déjà en cours pour cette conversation.",
            )

        logger.info(f"Received message request for chat: {message_request.chat_id}")
        logger.info(f"User: {current_user.email}")
        logger.info(f"Is regeneration: {message_request.is_regeneration}")
        
        service = MessageService(db)
        user_message_id: Optional[str] = None
    
        logger.info(f"Validating chat ownership...")
        if not await service.validate_chat_user(message_request.chat_id, current_user.id):
            logger.error(f"Chat {message_request.chat_id} not authorized for user {current_user.id}")
            raise HTTPException(status_code=403, detail="Chat non autorisé")
        
        # Si c'est une régénération, supprimer le dernier message assistant
        if message_request.is_regeneration:
            logger.info("Handling regeneration - removing last assistant message")
            await service.delete_last_assistant_message(message_request.chat_id)
            # Ne pas recréer le message utilisateur, il existe déjà
        else:
            logger.info(f"Saving user message...")
            user_message = await service.create_message(
                chat_id=message_request.chat_id,
                role="user",
                content=message_request.content
            )
            user_message_id = str(user_message.id)
        
        chat = (await db.execute(
            select(Chat).where(Chat.id == message_request.chat_id)
        )).scalar_one_or_none()
        
        if chat:
            chat.last_message_at = func.now()
            await db.commit()
        
        logger.info(f"Getting chat history and agent...")
        chat_history = await service.get_chat_history(message_request.chat_id)
        agent = await service.get_chat_agent(message_request.chat_id)
        logger.info(f"History: {len(chat_history)} messages, Agent: {agent.name if agent else 'Default'}")
        
        logger.info(f"Calling Mistral AI...")
        # Injecter le contexte RAG dans le system prompt si fourni, sans l'enregistrer en base
        base_system = agent.system_prompt if agent else None

        ai_response, metadata = await service.generate_ai_response(
            messages=chat_history,
            system_prompt=base_system,
            chat_id=message_request.chat_id
        )
        logger.info(f"AI response received: {len(ai_response)} characters")
        
        logger.info(f"Saving assistant message...")
        assistant_message = await service.create_message(
            chat_id=message_request.chat_id,
            role="assistant",
            content=ai_response,
            model_used=metadata.get("model_used"),
            tokens_used=metadata.get("tokens_used"),
            processing_time=metadata.get("processing_time"),
            temperature=metadata.get("temperature")
        )
        
        logger.info(f"Message processing complete")
        return MessageResponse(
            id=str(assistant_message.id),
            role=assistant_message.role,
            content=assistant_message.content,
            created_at=assistant_message.created_at,
            chat_id=str(assistant_message.chat_id),
            tool_calls=metadata.get("tool_calls", None),
            user_message_id=user_message_id,
            is_edited=assistant_message.is_edited,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in send_message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if lock_token:
            await cache_service.release_lock(lock_key, lock_token)


@router.patch("/{message_id}", response_model=MessageResponse)
async def edit_message(
    message_id: str,
    edit_request: EditMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    service = MessageService(db)

    message = await service.get_message_with_chat(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message non trouvé")

    if message.role != "user":
        raise HTTPException(status_code=400, detail="Seuls les messages utilisateur peuvent être modifiés")

    chat_id = str(message.chat_id)
    if not await user_has_permission(db, current_user, PERM_MESSAGE_EDIT_OWN):
        raise HTTPException(status_code=403, detail="You are not allowed to edit messages")
    if not await service.validate_chat_user(chat_id, current_user.id):
        raise HTTPException(status_code=403, detail="Chat non autorisé")

    updated_message = await service.update_user_message_content(message, edit_request.content)

    return MessageResponse(
        id=str(updated_message.id),
        role=updated_message.role,
        content=updated_message.content,
        created_at=updated_message.created_at,
        chat_id=str(updated_message.chat_id),
        feedback=None,
        tool_calls=None,
        is_edited=updated_message.is_edited,
        user_message_id=str(updated_message.id),
    )

@router.post("/stream")
@limiter.limit(AI_RATE_LIMIT)
async def stream_message(
    request: Request,
    message_request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    logger = logging.getLogger(__name__)
    service = MessageService(db)

    chat_id = message_request.chat_id
    lock_key = cache_service.generate_key("chat_lock", chat_id)
    lock_token: Optional[str] = None

    async def event_generator():
        user_message_id = None
        assistant_message_id = None
        tool_calls: list[str] | None = None

        try:
            if not await user_has_permission(db, current_user, PERM_MESSAGE_SEND):
                raise HTTPException(status_code=403, detail="You are not allowed to send messages")
            nonlocal lock_token

            lock_token = await cache_service.acquire_lock(lock_key, ttl_seconds=300)
            if lock_token is None:
                logger.warning("Concurrent stream_message detected for chat %s", chat_id)
                error_payload = {
                    "type": "error",
                    "error": "Une génération est déjà en cours pour cette conversation.",
                }
                yield f"data: {json.dumps(error_payload)}\n\n"
                return

            if not await service.validate_chat_user(chat_id, current_user.id):
                raise HTTPException(status_code=403, detail="Chat non autorisé")

            chat = (
                await db.execute(
                    select(Chat).where(Chat.id == message_request.chat_id)
                )
            ).scalar_one_or_none()

            if chat:
                chat.last_message_at = func.now()
                await db.commit()

            agent = await service.get_chat_agent(chat_id)
            base_system = agent.system_prompt if agent else None

            if message_request.is_regeneration:
                logger.info("Streaming regeneration requested for chat %s", chat_id)
                await service.delete_last_assistant_message(chat_id)
            else:
                logger.info("Streaming new message for chat %s", chat_id)
                user_message = await service.create_message(chat_id, "user", message_request.content)
                user_message_id = str(user_message.id)

            yield f"data: {json.dumps({'type': 'start', 'user_message_id': user_message_id})}\n\n"

            history = await service.get_chat_history(chat_id)

            full_response = ""
            async for chunk in service.generate_ai_stream_response(
                messages=history,
                system_prompt=base_system,
                chat_id=chat_id
            ):
                if chunk == "[[TOOL_CHECK]]":
                    yield f"data: {json.dumps({'type': 'tool_check'})}\n\n"
                elif chunk == "[[POWERPOINT_GENERATION]]":
                    tool_calls = ["generate_powerpoint_from_text"]
                    yield f"data: {json.dumps({'type': 'powerpoint_generation'})}\n\n"
                elif not chunk.startswith("[["):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

            assistant_message = await service.create_message(chat_id, "assistant", full_response)
            assistant_message_id = str(assistant_message.id)

            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message_id, 'tool_calls': tool_calls})}\n\n"

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error during streaming: %s", e, exc_info=True)
            error_payload = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_payload)}\n\n"
        finally:
            if lock_token:
                await cache_service.release_lock(lock_key, lock_token)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/{message_id}/feedback", response_model=MessageFeedbackResponse)
async def set_message_feedback(
    message_id: str,
    feedback_request: MessageFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    service = FeedbackService(db)
    if not await user_has_permission(db, current_user, PERM_MESSAGE_FEEDBACK):
        raise HTTPException(status_code=403, detail="You are not allowed to set message feedback")

    feedback_entry = await service.set_feedback(
        message_id=message_id,
        user_id=current_user.id,
        feedback_type=feedback_request.feedback,
    )

    return MessageFeedbackResponse(
        message_id=str(feedback_entry.message_id),
        feedback=feedback_entry.feedback_type,
    )
