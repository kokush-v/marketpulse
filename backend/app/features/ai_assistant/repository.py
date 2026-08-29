import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai_assistant.models import AssistantConversation, AssistantMessage


class AssistantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_conversation(
        self,
        *,
        user_id: uuid.UUID,
        title: str | None,
    ) -> AssistantConversation:
        conversation = AssistantConversation(user_id=user_id, title=title)
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def list_conversations_for_user(self, user_id: uuid.UUID) -> list[AssistantConversation]:
        result = await self.session.execute(
            select(AssistantConversation)
            .where(AssistantConversation.user_id == user_id)
            .order_by(
                AssistantConversation.updated_at.desc(),
                AssistantConversation.created_at.desc(),
            )
        )
        return list(result.scalars().all())

    async def get_conversation_for_user(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> AssistantConversation | None:
        result = await self.session.execute(
            select(AssistantConversation).where(
                AssistantConversation.id == conversation_id,
                AssistantConversation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_messages_for_conversation(
        self,
        conversation_id: uuid.UUID,
    ) -> list[AssistantMessage]:
        result = await self.session.execute(
            select(AssistantMessage)
            .where(AssistantMessage.conversation_id == conversation_id)
            .order_by(AssistantMessage.sequence.asc())
        )
        return list(result.scalars().all())

    async def update_conversation_title(
        self,
        *,
        conversation: AssistantConversation,
        title: str,
    ) -> AssistantConversation:
        conversation.title = title
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def delete_conversation(self, *, conversation: AssistantConversation) -> None:
        await self.session.delete(conversation)
        await self.session.commit()

    async def append_message(
        self,
        *,
        conversation: AssistantConversation,
        role: str,
        content: str,
        suggested_replies: list[str] | None = None,
        chart_payload: dict[str, object] | None = None,
        initial_title: str | None = None,
    ) -> AssistantMessage:
        await self.session.refresh(conversation, with_for_update=True)
        sequence_result = await self.session.execute(
            select(func.coalesce(func.max(AssistantMessage.sequence), -1)).where(
                AssistantMessage.conversation_id == conversation.id
            )
        )
        last_sequence = int(sequence_result.scalar_one())
        message = AssistantMessage(
            conversation_id=conversation.id,
            sequence=last_sequence + 1,
            role=role,
            content=content,
            suggested_replies=suggested_replies or [],
            chart_payload=chart_payload,
        )
        self.session.add(message)
        if role == "user" and last_sequence == -1 and conversation.title is None:
            conversation.title = initial_title
        conversation.updated_at = func.now()
        await self.session.commit()
        await self.session.refresh(conversation)
        await self.session.refresh(message)
        return message
