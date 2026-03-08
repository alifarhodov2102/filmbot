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
        # 1. Bot obyektini va foydalanuvchi ma'lumotlarini olish
        bot = data['bot']
        user_id = event.from_user.id

        # 2. Adminlar uchun majburiy obuna tekshiruvini o'tkazib yuborish
        if user_id in ADMINS:
            return await handler(event, data)

        # 3. Faqat matnli xabarlarni va buyruqlarni tekshiramiz
        if not event.text:
            return await handler(event, data)

        # 4. /start buyrug'i uchun tekshiruvni o'tkazib yuboramiz
        # Bu foydalanuvchiga birinchi bo'lib salomlashish xabarini ko'rishga imkon beradi
        if event.text.startswith("/start"):
            return await handler(event, data)

        # 5. Faqat foydalanuvchi kod (faqat raqamlar) yuborganda obunani tekshiramiz
        if event.text.isdigit():
            not_joined_channels = []
            
            # Har bir kanalni birma-bir tekshirib chiqamiz
            for channel_id in CHANNELS:
                try:
                    member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                    
                    # Ruxsat berilgan statuslar: a'zo, admin yoki yaratuvchi
                    allowed_statuses = ['member', 'administrator', 'creator']
                    
                    if member.status not in allowed_statuses:
                        not_joined_channels.append(channel_id)
                        
                except Exception as e:
                    # Agar bot kanalda admin bo'lmasa yoki kanal topilmasa
                    not_joined_channels.append(channel_id)
                    print(f"Obuna tekshirishda xatolik (ID: {channel_id}): {e}")

            # 6. Agar foydalanuvchi kamida bitta kanalga a'zo bo'lmagan bo'lsa
            if not_joined_channels:
                invite_links = []
                
                # Majburiy kanallarning taklif linklarini shakllantiramiz
                for ch_id in CHANNELS:
                    try:
                        chat = await bot.get_chat(ch_id)
                        # Username bo'lsa t.me/link, bo'lmasa invite_link ishlatiladi
                        link = chat.invite_link or f"https://t.me/{chat.username}"
                        invite_links.append(link)
                    except Exception:
                        # Fallback link (agar bot kanal ma'lumotini ololmasa)
                        continue

                # Foydalanuvchiga kanallar ro'yxati va tugmani ko'rsatamiz
                await event.answer(
                    "❗ <b>Kinolarni ko'rish uchun barcha kanallarimizga a'zo bo'lishingiz shart!</b>\n\n"
                    "Iltimos, pastdagi kanallarga qo'shiling va <b>'Tasdiqlash ✅'</b> tugmasini bosing.",
                    reply_markup=get_join_inline(invite_links)
                )
                return  # Kodni handlers'ga o'tkazmaymiz, jarayonni shu yerda to'xtatamiz

        # 7. Hamma kanalda bo'lsa yoki xabar raqamli kod bo'lmasa, handlers'ga yuboramiz
        return await handler(event, data)