from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from config import CHANNELS, ADMINS
from keyboards import get_join_inline

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # 1. Bot obyektini va foydalanuvchi ID sini olish
        bot = data['bot']
        user_id = event.from_user.id

        # 2. Adminlar uchun tekshiruvni o'tkazib yuborish
        if user_id in ADMINS:
            return await handler(event, data)

        # 3. Faqat matnli xabarlarni tekshiramiz
        if not event.text:
            return await handler(event, data)

        # 4. /start buyrug'i uchun tekshiruvni o'tkazib yuboramiz
        if event.text.startswith("/start"):
            return await handler(event, data)

        # 5. Faqat foydalanuvchi kino kodi (faqat raqamlar) yuborganda tekshiramiz
        if event.text.isdigit():
            not_joined_channels = []
            
            # Har bir kanalni birma-bir tekshirib chiqamiz
            for channel_id in CHANNELS:
                try:
                    member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                    
                    # Ruxsat berilgan statuslar
                    allowed_statuses = ['member', 'administrator', 'creator']
                    
                    if member.status not in allowed_statuses:
                        not_joined_channels.append(channel_id)
                        
                except Exception as e:
                    # Agar bot kanalda admin bo'lmasa yoki foydalanuvchi topilmasa
                    not_joined_channels.append(channel_id)
                    print(f"Xatolik (ID: {channel_id}): {e}")

            # 6. Agar foydalanuvchi bitta bo'lsa ham kanalga a'zo bo'lmagan bo'lsa
            if not_joined_channels:
                invite_links = []
                
                # Barcha majburiy kanallarning taklif linklarini yig'amiz
                for ch_id in CHANNELS:
                    try:
                        chat = await bot.get_chat(ch_id)
                        link = chat.invite_link or f"https://t.me/{chat.username}"
                        invite_links.append(link)
                    except Exception:
                        continue

                # Ikkala kanal tugmasi bilan javob qaytaramiz
                await event.answer(
                    "❗ <b>Kinolarni ko'rish uchun barcha kanallarimizga a'zo bo'lishingiz shart!</b>\n\n"
                    "Iltimos, pastdagi kanallarga qo'shiling va <b>'Tasdiqlash ✅'</b> tugmasini bosing.",
                    reply_markup=get_join_inline(invite_links)
                )
                return  # Kino kodini qayta ishlashni to'xtatamiz

        # 7. Hamma kanalda bo'lsa yoki xabar raqam bo'lmasa, davom etadi
        return await handler(event, data)
