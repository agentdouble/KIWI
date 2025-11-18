from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
import uuid

class FeedbackLoop(Base):
    __tablename__ = "feedbackloop"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    feedback_type = Column(String(10), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('message_id', 'user_id', name='uq_feedbackloop_message_user'),
        CheckConstraint(feedback_type.in_(['up', 'down']), name='check_feedbackloop_type'),
    )

    message = relationship("Message", back_populates="feedback_entries")
    user = relationship("User", back_populates="feedback_entries")

    def __repr__(self):
        return (
            f"<FeedbackLoop(id={self.id}, message_id={self.message_id}, "
            f"user_id={self.user_id}, feedback_type={self.feedback_type})>"
        )
