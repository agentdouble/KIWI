from typing import Iterable
from uuid import UUID
import uuid

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.feedback_loop import FeedbackLoop
from app.models.message import Message


class FeedbackService:
    """Service layer handling persistence for message feedback entries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_message_for_user(self, message_id: UUID, user_id: UUID) -> Message:
        query = (
            select(Message)
            .join(Chat, Message.chat_id == Chat.id)
            .where(and_(Message.id == message_id, Chat.user_id == user_id))
        )
        result = await self.db.execute(query)
        message = result.scalar_one_or_none()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message introuvable pour cet utilisateur"
            )
        return message

    async def set_feedback(self, message_id: str, user_id: UUID, feedback_type: str) -> FeedbackLoop:
        feedback_value = feedback_type.lower()
        if feedback_value not in {"up", "down"}:
            raise HTTPException(status_code=400, detail="Type de feedback invalide")

        message_uuid = uuid.UUID(message_id)
        await self._get_message_for_user(message_uuid, user_id)

        query = (
            select(FeedbackLoop)
            .where(and_(FeedbackLoop.message_id == message_uuid, FeedbackLoop.user_id == user_id))
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            existing.feedback_type = feedback_value
            feedback_entry = existing
        else:
            feedback_entry = FeedbackLoop(
                message_id=message_uuid,
                user_id=user_id,
                feedback_type=feedback_value,
            )
            self.db.add(feedback_entry)

        await self.db.commit()
        await self.db.refresh(feedback_entry)
        return feedback_entry

    async def get_feedback_for_messages(self, message_ids: Iterable[UUID], user_id: UUID) -> dict[UUID, str]:
        if not message_ids:
            return {}

        query = (
            select(FeedbackLoop)
            .where(
                and_(
                    FeedbackLoop.message_id.in_(list(message_ids)),
                    FeedbackLoop.user_id == user_id,
                )
            )
        )
        result = await self.db.execute(query)
        feedback_entries = result.scalars().all()
        return {entry.message_id: entry.feedback_type for entry in feedback_entries}

    async def delete_feedback(self, message_id: str, user_id: UUID) -> None:
        message_uuid = uuid.UUID(message_id)
        await self._get_message_for_user(message_uuid, user_id)

        query = (
            select(FeedbackLoop)
            .where(and_(FeedbackLoop.message_id == message_uuid, FeedbackLoop.user_id == user_id))
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            await self.db.delete(existing)
            await self.db.commit()
