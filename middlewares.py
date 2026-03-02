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
        # 1. Bot obyektini olish
        bot = data['bot']
        user_id = event.from_user.id

        # 2. Adminlar uchun tekshiruvni o'tkazib yuborish
        if user_id in ADMINS:
            return await handler(event, data)

        # 3. Faqat matnli xabarlarni tekshiramiz
        if not event.text:
            return await handler(event, data)

        # 4. /start buyrug'i uchun tekshiruvni o'tkazib yuboramiz
        # Bu foydalanuvchiga birinchi bo'lib tabrik xabarini ko'rishga ruxsat beradi
        if event.text.startswith("/start"):
            return await handler(event, data)

        # 5. Faqat foydalanuvchi kino kodi (faqat raqamlar) yuborganda tekshiramiz
        if event.text.isdigit():
            try:
                # Kanalga a'zolikni tekshirish
                member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
                
                # Ruxsat berilgan statuslar
                allowed_statuses = ['member', 'administrator', 'creator']
                
                if member.status in allowed_statuses:
                    return await handler(event, data)
                
            except Exception as e:
                # Agar bot kanalda admin bo'lmasa yoki boshqa xato bo'lsa
                print(f"Obunani tekshirishda xatolik: {e}")

            # 6. Agar a'zo bo'lmasa, taklif linkini olib tugmani ko'rsatish
            try:
                chat = await bot.get_chat(CHANNEL_ID)
                invite_link = chat.invite_link or f"https://t.me/{chat.username}"
            except Exception:
                # Xatolik yuz bersa, config-dagi fallback link
                invite_link = "https://t.me/your_channel_username" 

            await event.answer(
                "❗ <b>Kinolarni ko'rish uchun kanalimizga a'zo bo'lishingiz shart!</b>\n\n"
                "Kanalga qo'shiling va <b>'Tasdiqlash ✅'</b> tugmasini bosing.",
                reply_markup=get_join_inline(invite_link)
            )
            return  # Kino kodiga javob bermaymiz

        # 7. Agar xabar raqam bo'lmasa (masalan, shunchaki matn), oddiy ishlayveradi
        return await handler(event, data)
