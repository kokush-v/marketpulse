from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.core.config import settings
from app.features.telegram.schemas import TelegramBotResult

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


class TelegramBotApp:
    def __init__(self, service_factory: ServiceFactory) -> None:
        self._service_factory = service_factory
        self._bot = Bot(token=settings.telegram_bot_token)
        self._dispatcher = Dispatcher()
        self._bot_username: str | None = None
        router = Router()

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
                await message.answer(result.message, reply_markup=keyboard)
                return

            await message.answer(result.message)

        @router.message(CommandStart())
        async def handle_plain_start(message: Message) -> None:
            await message.answer(
                "Start Telegram linking from the MarketPulse web app, "
                "then open the bot using the generated link."
            )

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

            await callback.answer("Unknown action", show_alert=False)

        self._dispatcher.include_router(router)

    async def initialize(self) -> None:
        if settings.telegram_bot_token == "replace-me":
            logger.info("Telegram bot startup skipped: TELEGRAM_BOT_TOKEN is not configured.")
            return

        me = await self._bot.get_me()
        self._bot_username = me.username or settings.telegram_bot_username
        logger.info("%s is ready", self._bot_username)

    async def shutdown(self) -> None:
        await self._bot.session.close()

    async def handle_update(self, payload: dict[str, object]) -> None:
        await self._dispatcher.feed_raw_update(self._bot, payload)

    async def send_message(self, *, chat_id: int, text: str) -> None:
        await self._bot.send_message(chat_id=chat_id, text=text)
