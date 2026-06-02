from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from app.core.config import settings
from app.features.telegram.schemas import TelegramBotProfile, TelegramBotResult

ServiceFactory = Callable[[], AsyncIterator["TelegramBotFlowService"]]
logger = logging.getLogger("uvicorn.error")


class TelegramBotFlowService:
    async def consume_start_token(
        self,
        *,
        token: str,
        telegram_user_id: int,
        telegram_chat_id: int,
        telegram_username: str | None,
        confirmed_switch: bool,
    ) -> TelegramBotResult:
        raise NotImplementedError

    async def cancel_switch(self, *, token: str) -> TelegramBotResult:
        raise NotImplementedError

    async def get_profile(
        self,
        *,
        telegram_user_id: int,
    ) -> tuple[TelegramBotResult, TelegramBotProfile | None]:
        raise NotImplementedError

    async def request_unlink(self, *, telegram_user_id: int) -> TelegramBotResult:
        raise NotImplementedError

    async def confirm_unlink(self, *, telegram_user_id: int) -> TelegramBotResult:
        raise NotImplementedError

    async def cancel_unlink(self, *, telegram_user_id: int) -> TelegramBotResult:
        raise NotImplementedError


class TelegramBotApp:
    def __init__(self, service_factory: ServiceFactory) -> None:
        self._service_factory = service_factory
        self._bot: Bot | None = None
        self._dispatcher = Dispatcher()
        self._bot_username: str | None = None
        router = Router()

        def _main_menu_keyboard() -> ReplyKeyboardMarkup:
            return ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Profile")]],
                resize_keyboard=True,
            )

        @router.message(CommandStart(deep_link=True))
        async def handle_start(message: Message, command: CommandObject) -> None:
            token = command.args or ""
            async with self._service_factory() as service:
                result = await service.consume_start_token(
                    token=token,
                    telegram_user_id=message.from_user.id,
                    telegram_chat_id=message.chat.id,
                    telegram_username=message.from_user.username,
                    confirmed_switch=False,
                )
            if result.requires_confirmation:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Confirm switch",
                                callback_data=f"tg-switch-confirm:{token}",
                            ),
                            InlineKeyboardButton(
                                text="Keep current account",
                                callback_data=f"tg-switch-cancel:{token}",
                            ),
                        ]
                    ]
                )
                await message.answer(
                    result.message,
                    reply_markup=keyboard,
                )
                return

            await message.answer(result.message, reply_markup=_main_menu_keyboard())

        @router.message(CommandStart())
        async def handle_plain_start(message: Message) -> None:
            await message.answer(
                "Start Telegram linking from the MarketPulse web app, "
                "then open the bot using the generated link.",
                reply_markup=_main_menu_keyboard(),
            )

        @router.message(F.text == "Profile")
        async def handle_profile(message: Message) -> None:
            async with self._service_factory() as service:
                result, profile = await service.get_profile(telegram_user_id=message.from_user.id)

            if profile is None:
                await message.answer(result.message, reply_markup=_main_menu_keyboard())
                return

            unlink_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Unlink Profile",
                            callback_data="tg-unlink-request",
                        )
                    ]
                ]
            )
            profile_text = (
                f"Profile\n\nDisplay name: {profile.display_name}\nEmail: {profile.email}"
            )
            if profile.avatar_url:
                await message.answer_photo(
                    photo=profile.avatar_url,
                    caption=profile_text,
                    reply_markup=unlink_markup,
                )
                return

            await message.answer(profile_text, reply_markup=unlink_markup)

        @router.callback_query()
        async def handle_callback(callback: CallbackQuery) -> None:
            data = callback.data or ""
            if data.startswith("tg-switch-confirm:"):
                token = data.removeprefix("tg-switch-confirm:")
                async with self._service_factory() as service:
                    result = await service.consume_start_token(
                        token=token,
                        telegram_user_id=callback.from_user.id,
                        telegram_chat_id=(
                            callback.message.chat.id if callback.message else callback.from_user.id
                        ),
                        telegram_username=callback.from_user.username,
                        confirmed_switch=True,
                    )
                await callback.answer()
                if callback.message is not None:
                    await callback.message.edit_text(result.message)
                return

            if data.startswith("tg-switch-cancel:"):
                token = data.removeprefix("tg-switch-cancel:")
                async with self._service_factory() as service:
                    result = await service.cancel_switch(token=token)
                await callback.answer()
                if callback.message is not None:
                    await callback.message.edit_text(result.message)
                return

            if data == "tg-unlink-request":
                async with self._service_factory() as service:
                    result = await service.request_unlink(telegram_user_id=callback.from_user.id)
                await callback.answer()
                if callback.message is not None:
                    if result.requires_confirmation:
                        keyboard = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text="Confirm unlink",
                                        callback_data="tg-unlink-confirm",
                                    ),
                                    InlineKeyboardButton(
                                        text="Keep linked",
                                        callback_data="tg-unlink-cancel",
                                    ),
                                ]
                            ]
                        )
                        await callback.message.answer(
                            result.message,
                            reply_markup=keyboard,
                        )
                    else:
                        await callback.message.answer(result.message)
                return

            if data == "tg-unlink-confirm":
                async with self._service_factory() as service:
                    result = await service.confirm_unlink(telegram_user_id=callback.from_user.id)
                await callback.answer()
                if callback.message is not None:
                    await callback.message.edit_text(result.message)
                return

            if data == "tg-unlink-cancel":
                async with self._service_factory() as service:
                    result = await service.cancel_unlink(telegram_user_id=callback.from_user.id)
                await callback.answer()
                if callback.message is not None:
                    await callback.message.edit_text(result.message)
                return

            await callback.answer("Unknown action", show_alert=False)

        self._dispatcher.include_router(router)

    def _token_is_configured(self) -> bool:
        token = settings.telegram_bot_token.strip()
        return bool(token) and token != "replace-me" and ":" in token

    def _get_bot(self) -> Bot:
        if self._bot is None:
            self._bot = Bot(token=settings.telegram_bot_token)
        return self._bot

    async def initialize(self) -> None:
        if not self._token_is_configured():
            logger.info("Telegram bot startup skipped: TELEGRAM_BOT_TOKEN is not configured.")
            return

        self._bot_username = settings.telegram_bot_username
        logger.info("%s is ready", self._bot_username)

    async def shutdown(self) -> None:
        if self._bot is not None:
            await self._bot.session.close()

    async def handle_update(self, payload: dict[str, object]) -> None:
        if not self._token_is_configured():
            raise RuntimeError("Telegram bot is not configured.")
        await self._dispatcher.feed_raw_update(self._get_bot(), payload)

    async def send_message(self, *, chat_id: int, text: str) -> int:
        if not self._token_is_configured():
            raise RuntimeError("Telegram bot is not configured.")
        message = await self._get_bot().send_message(chat_id=chat_id, text=text)
        return message.message_id

    async def delete_message(self, *, chat_id: int, message_id: int) -> None:
        if not self._token_is_configured():
            raise RuntimeError("Telegram bot is not configured.")
        await self._get_bot().delete_message(chat_id=chat_id, message_id=message_id)
