from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from config import CHANNEL_ID, ADMINS
from keyboards import get_join_inline

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # 1. Get the bot instance
        bot = data['bot']
        user_id = event.from_user.id

        # 2. Skip check for Admins so you don't get blocked from your own bot
        if user_id in ADMINS:
            return await handler(event, data)

        # 3. Handle only text messages (skip for buttons/other updates)
        if not event.text:
            return await handler(event, data)

        try:
            # 4. Check membership status
            member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            
            # Statuses that are allowed to pass
            allowed_statuses = ['member', 'administrator', 'creator']
            
            if member.status in allowed_statuses:
                return await handler(event, data)
            
        except Exception as e:
            # This triggers if the user hasn't started the bot or bot isn't admin in channel
            print(f"Subscription check error: {e}")

        # 5. If not joined, fetch invite link and send keyboard
        try:
            chat = await bot.get_chat(CHANNEL_ID)
            invite_link = chat.invite_link or f"https://t.me/{chat.username}"
        except Exception:
            invite_link = "https://t.me/+R80-yTSvEb4yZDYy" # Fallback link

        await event.answer(
            "❗ <b>Access Denied</b>\n\n"
            "You must join our channel to use this bot and watch movies! "
            "After joining, click the 'I have joined' button.",
            reply_markup=get_join_inline(invite_link)
        )
        return  # Stop the execution so the user's message is ignored
