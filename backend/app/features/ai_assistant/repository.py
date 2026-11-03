import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ai_assistant.models import (
    AssistantConversation,
    AssistantMessage,
    AssistantMessageFeedback,
    AssistantPendingAction,
)


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

    async def get_message_for_user(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> AssistantMessage | None:
        result = await self.session.execute(
            select(AssistantMessage)
            .join(
                AssistantConversation,
                AssistantConversation.id == AssistantMessage.conversation_id,
            )
            .where(
                AssistantMessage.id == message_id,
                AssistantMessage.conversation_id == conversation_id,
                AssistantConversation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_message_feedback(
        self,
        *,
        message: AssistantMessage,
        user_id: uuid.UUID,
        rating: str,
        reason: str | None,
    ) -> AssistantMessageFeedback:
        feedback = AssistantMessageFeedback(
            message_id=message.id,
            user_id=user_id,
            rating=rating,
            reason=reason,
        )
        message.feedback = feedback
        self.session.add(feedback)
        await self.session.commit()
        await self.session.refresh(feedback)
        return feedback

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
        pending_action: dict[str, object] | None = None,
        sources: list[dict[str, object]] | None = None,
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
            pending_action=pending_action,
            sources=sources,
        )
        self.session.add(message)
        if role == "user" and last_sequence == -1 and conversation.title is None:
            conversation.title = initial_title
        conversation.updated_at = func.now()
        await self.session.commit()
        await self.session.refresh(conversation)
        await self.session.refresh(message)
        return message

    async def create_pending_action(
        self,
        *,
        conversation: AssistantConversation,
        user_id: uuid.UUID,
        action_type: str,
        target_id: str,
        validated_input: dict[str, object],
        display_summary: dict[str, object],
        expires_at: datetime,
    ) -> AssistantPendingAction:
        existing_actions = list(
            (
                await self.session.execute(
                    select(AssistantPendingAction)
                    .where(
                        AssistantPendingAction.conversation_id == conversation.id,
                        AssistantPendingAction.user_id == user_id,
                        AssistantPendingAction.status == "pending",
                    )
                    .with_for_update()
                )
            )
            .scalars()
            .all()
        )
        for existing_action in existing_actions:
            existing_action.status = "cancelled"
            existing_action.resolved_at = func.now()
            await self._update_action_message_status(existing_action, "cancelled")
        action = AssistantPendingAction(
            conversation_id=conversation.id,
            user_id=user_id,
            action_type=action_type,
            target_id=target_id,
            validated_input=validated_input,
            display_summary=display_summary,
            expires_at=expires_at,
        )
        self.session.add(action)
        await self.session.commit()
        await self.session.refresh(action)
        return action

    async def link_pending_action_message(
        self,
        *,
        action: AssistantPendingAction,
        message: AssistantMessage,
        pending_action: dict[str, object],
    ) -> None:
        action.message_id = message.id
        message.pending_action = pending_action
        await self.session.commit()

    async def get_pending_action_for_user(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        action_id: uuid.UUID,
    ) -> AssistantPendingAction | None:
        result = await self.session.execute(
            select(AssistantPendingAction).where(
                AssistantPendingAction.id == action_id,
                AssistantPendingAction.user_id == user_id,
                AssistantPendingAction.conversation_id == conversation_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_current_pending_action_for_user(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> AssistantPendingAction | None:
        result = await self.session.execute(
            select(AssistantPendingAction)
            .where(
                AssistantPendingAction.user_id == user_id,
                AssistantPendingAction.conversation_id == conversation_id,
                AssistantPendingAction.status == "pending",
            )
            .order_by(AssistantPendingAction.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def claim_pending_action(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        action_id: uuid.UUID,
    ) -> AssistantPendingAction | None:
        result = await self.session.execute(
            select(AssistantPendingAction)
            .where(
                AssistantPendingAction.id == action_id,
                AssistantPendingAction.user_id == user_id,
                AssistantPendingAction.conversation_id == conversation_id,
            )
            .with_for_update()
        )
        action = result.scalar_one_or_none()
        if action is None:
            return None
        if action.status != "pending":
            return action
        if action.expires_at <= datetime.now(UTC):
            action.status = "expired"
            action.resolved_at = func.now()
            await self._update_action_message_status(action, "expired")
            await self.session.commit()
            return action
        action.status = "executing"
        await self.session.commit()
        return action

    async def resolve_pending_action(
        self,
        *,
        action: AssistantPendingAction,
        status: str,
    ) -> None:
        action.status = status
        action.resolved_at = func.now()
        await self._update_action_message_status(action, status)
        await self.session.commit()

    async def cancel_pending_action(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        action_id: uuid.UUID,
    ) -> AssistantPendingAction | None:
        action = await self.claim_pending_action(
            user_id=user_id,
            conversation_id=conversation_id,
            action_id=action_id,
        )
        if action is None or action.status != "executing":
            return action
        await self.resolve_pending_action(action=action, status="cancelled")
        return action

    async def _update_action_message_status(
        self,
        action: AssistantPendingAction,
        status: str,
    ) -> None:
        if action.message_id is None:
            return
        result = await self.session.execute(
            select(AssistantMessage).where(AssistantMessage.id == action.message_id)
        )
        message = result.scalar_one_or_none()
        if message is not None and message.pending_action is not None:
            message.pending_action = {**message.pending_action, "status": status}
