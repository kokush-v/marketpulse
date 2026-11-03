from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from app.features.ai_assistant.schemas import (
    AssistantConversationListResponse,
    AssistantConversationResponse,
    AssistantErrorResponse,
    AssistantMessageFeedbackResponse,
    CreateAssistantConversationRequest,
    SendAssistantMessageRequest,
    SubmitAssistantMessageFeedbackRequest,
    UpdateAssistantConversationRequest,
)
from app.features.ai_assistant.service import AssistantService, AssistantServiceError
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User

router = APIRouter(prefix="/assistant", tags=["ai-assistant"])
current_user_dependency = Depends(get_current_user)


def _service_error_response(error: AssistantServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=AssistantErrorResponse(
            code=error.code,
            message=error.message,
            retryable=error.retryable,
            retry_after_seconds=error.retry_after_seconds,
        ).model_dump(),
    )


@router.get("/conversations", response_model=AssistantConversationListResponse)
async def list_conversations(
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AssistantService, Depends()],
) -> AssistantConversationListResponse:
    return await service.list_conversations(current_user)


@router.post(
    "/conversations",
    response_model=AssistantConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: CreateAssistantConversationRequest,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AssistantService, Depends()],
) -> AssistantConversationResponse:
    return await service.create_conversation(current_user, payload)


@router.get(
    "/conversations/{conversation_id}",
    response_model=AssistantConversationResponse,
    responses={404: {"model": AssistantErrorResponse}},
)
async def get_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AssistantService, Depends()],
) -> AssistantConversationResponse:
    try:
        return await service.get_conversation(current_user, conversation_id)
    except AssistantServiceError as error:
        return _service_error_response(error)


@router.patch(
    "/conversations/{conversation_id}",
    response_model=AssistantConversationResponse,
    responses={
        404: {"model": AssistantErrorResponse},
        422: {"model": AssistantErrorResponse},
    },
)
async def update_conversation_title(
    conversation_id: UUID,
    payload: UpdateAssistantConversationRequest,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AssistantService, Depends()],
) -> AssistantConversationResponse:
    try:
        return await service.update_conversation_title(current_user, conversation_id, payload)
    except AssistantServiceError as error:
        return _service_error_response(error)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": AssistantErrorResponse}},
)
async def delete_conversation(
    conversation_id: UUID,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AssistantService, Depends()],
) -> Response:
    try:
        await service.delete_conversation(current_user, conversation_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except AssistantServiceError as error:
        return _service_error_response(error)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=AssistantConversationResponse,
    responses={
        404: {"model": AssistantErrorResponse},
        422: {"model": AssistantErrorResponse},
        429: {"model": AssistantErrorResponse},
        503: {"model": AssistantErrorResponse},
        504: {"model": AssistantErrorResponse},
    },
)
async def send_message(
    conversation_id: UUID,
    payload: SendAssistantMessageRequest,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AssistantService, Depends()],
) -> AssistantConversationResponse:
    try:
        return await service.send_message(current_user, conversation_id, payload)
    except AssistantServiceError as error:
        return _service_error_response(error)


@router.post(
    "/conversations/{conversation_id}/messages/{message_id}/feedback",
    response_model=AssistantMessageFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Rate an assistant response",
    responses={
        404: {"model": AssistantErrorResponse},
        409: {"model": AssistantErrorResponse},
        422: {"model": AssistantErrorResponse},
    },
)
async def submit_message_feedback(
    conversation_id: UUID,
    message_id: UUID,
    payload: SubmitAssistantMessageFeedbackRequest,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AssistantService, Depends()],
) -> AssistantMessageFeedbackResponse:
    try:
        return await service.submit_message_feedback(
            current_user, conversation_id, message_id, payload
        )
    except AssistantServiceError as error:
        return _service_error_response(error)


@router.post(
    "/conversations/{conversation_id}/pending-actions/{action_id}/confirm",
    response_model=AssistantConversationResponse,
    responses={404: {"model": AssistantErrorResponse}, 409: {"model": AssistantErrorResponse}},
)
async def confirm_pending_action(
    conversation_id: UUID,
    action_id: UUID,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AssistantService, Depends()],
) -> AssistantConversationResponse:
    try:
        return await service.confirm_pending_action(current_user, conversation_id, action_id)
    except AssistantServiceError as error:
        return _service_error_response(error)


@router.post(
    "/conversations/{conversation_id}/pending-actions/{action_id}/cancel",
    response_model=AssistantConversationResponse,
    responses={404: {"model": AssistantErrorResponse}, 409: {"model": AssistantErrorResponse}},
)
async def cancel_pending_action(
    conversation_id: UUID,
    action_id: UUID,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AssistantService, Depends()],
) -> AssistantConversationResponse:
    try:
        return await service.cancel_pending_action(current_user, conversation_id, action_id)
    except AssistantServiceError as error:
        return _service_error_response(error)
