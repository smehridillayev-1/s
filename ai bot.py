import logging
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Yangi bepul va kalitsiz AI kutubxonasi
import g4f
from g4f.client import Client

# ==========================================
# ⚙️ SOZLAMALAR VA TOKNLAR
# ==========================================
BOT_TOKEN = "8186923406:AAFYezQm-23QVvcX6nI3b1oeQNTPIz_bqrY"
REQUIRED_CHANNEL = "@rahmatillayevch"  # Bot kanalda admin bo'lishi shart
ADMIN_ID = 8004582786

# Foydalanuvchilar bazasi
USERS_DB = {}

# Obyektlarni yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler()

# Kalitsiz AI mijozini yaratish
ai_client = Client()

logging.basicConfig(level=logging.INFO)


# ==========================================
# 🎭 NOODATIY SHRIFTLAR VA MATNLAR
# ==========================================
class TextStyles:
    @staticmethod
    def get_start_text(lang: str) -> str:
        if lang == "uz":
            return (
                "✨ 𝓢𝓪𝓶𝓪𝓷𝓭𝓪𝓻 𝓜𝓮𝓱𝓻𝓲𝓭𝓲𝓵𝓵𝓪𝔂𝓮𝝿 𝓫𝓸𝓽𝓲𝓰𝓪 𝔁𝓾𝓼𝓱 𝓴𝓮𝓵𝓲𝓫𝓼𝓲𝔃! ✨\n\n"
                "🪐 *Koinotning eng aqlli sun'iy intellekt tizimiga ulandingiz.*\n"
                "💭 Menga xohlagan savolingizni bering, men sizga ajoyib javoblar qaytaraman!"
            )
        elif lang == "ru":
            return (
                "✨ 𝓓𝓸𝓫𝓻𝓸 𝓹𝓸𝔃𝓱𝓪𝓵𝓸𝓿𝓪𝓽' 𝓿 𝓫𝓸𝓽 𝓢𝓪𝓶𝓪𝓷𝓭𝓪𝓻 𝓜𝓮𝓱𝓻𝓲𝓭𝓲𝓵𝓵𝓪𝔂𝓮𝝿! ✨\n\n"
                "🪐 *Вы подключились к самому умному ИИ.*\n"
                "💭 Задайте мне любой вопрос, и я дам вам невероятный ответ!"
            )
        else:  # en
            return (
                "✨ 𝓦𝓮𝓵𝓬𝓸𝓶𝓮 𝓽𝓸 𝓢𝓪𝓶𝓪𝓷𝓭𝓪𝓻 𝓜𝓮𝓱𝓻𝓲𝓭𝓲𝓵𝓵𝓪𝔂𝓮𝝿 𝓫𝓸𝓽! ✨\n\n"
                "🪐 *You have connected to the smartest AI system.*\n"
                "💭 Ask me any question, and I will give you an amazing response!"
            )

    @staticmethod
    def get_daily_text() -> str:
        return (
            "🚀 𝓝𝓮𝔀 𝓓𝓪𝔂 𝓝𝓮𝔀 𝓘𝓭𝓮𝓪𝓼 🚀\n\n"
            "🧠 *Kun davomida miyangizda ajoyib savollar tug'ildimi? Botimiz doim siz bilan! "
            "Keling, biror yangi narsani kashf etamiz.*\n\n"
            "👉 Botimizdan foydaning!"
        )


class BotStates(StatesGroup):
    choosing_language = State()
    main_chat = State()


# ==========================================
# 🛑 MAJBURIY OBUNA TEKSHIRUVI
# ==========================================
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except Exception:
        return False


def get_sub_keyboard(lang: str) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    btn_text = {"uz": "📢 Kanalga obuna bo'lish", "ru": "📢 Подписаться на канал", "en": "📢 Subscribe to Channel"}
    check_text = {"uz": "✅ Tekshirish", "ru": "✅ Проверить", "en": "✅ Check"}

    builder.button(text=btn_text.get(lang, "uz"), url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")
    builder.button(text=check_text.get(lang, "uz"), callback_data="check_sub")
    builder.adjust(1)
    return builder


# ==========================================
# 📥 START VA TIL TANLASH
# ==========================================
@dp.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    USERS_DB[user_id] = {"name": message.from_user.full_name, "lang": "uz"}

    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 O'zbekcha", callback_data="lang_uz")
    builder.button(text="🇷🇺 Русский", callback_data="lang_ru")
    builder.button(text="🇬🇧 English", callback_data="lang_en")
    builder.adjust(1)

    await message.answer(
        "👋 **Assalomu alaykum! / Здравствуйте! / Hello!**\n\n"
        "🌐 Iltimos, tilni tanlang / Пожалуйста, выберите язык / Please choose your language:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(BotStates.choosing_language)


@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id

    USERS_DB[user_id] = {"name": callback.from_user.full_name, "lang": lang}

    is_sub = await check_subscription(user_id)
    if not is_sub:
        msg = {
            "uz": "❌ Botdan foydalanish uchun kanalimizga a'zo bo'lishingiz shart!",
            "ru": "❌ Для использования бота необходимо подписаться на наш канал!",
            "en": "❌ You must subscribe to our channel to use the bot!"
        }
        await callback.message.edit_text(msg[lang], reply_markup=get_sub_keyboard(lang).as_markup())
        return

    await callback.message.edit_text(TextStyles.get_start_text(lang), parse_mode="Markdown")
    await state.set_state(BotStates.main_chat)


@dp.callback_query(F.data == "check_sub")
async def verify_sub(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = USERS_DB.get(user_id, {}).get("lang", "uz")

    if await check_subscription(user_id):
        await callback.message.edit_text(TextStyles.get_start_text(lang), parse_mode="Markdown")
        await state.set_state(BotStates.main_chat)
    else:
        await callback.answer("❌ Obuna bo'linmagan! / Не подписаны!", show_alert=True)


# ==========================================
# 🧠 BEPUL VA LIMITSIZ AI INTEGRATSIYASI (g4f)
# ==========================================
@dp.message(F.text)
async def ai_chat_handler(message: types.Message):
    user_id = message.from_user.id
    lang = USERS_DB.get(user_id, {}).get("lang", "uz")

    if not await check_subscription(user_id):
        msg = {"uz": "A'zolikni yangilang ❌", "ru": "Обновите подписку ❌", "en": "Check subscription ❌"}
        await message.answer(msg[lang], reply_markup=get_sub_keyboard(lang).as_markup())
        return

    waiting_msg = await message.answer("🔮 𝓣𝓱𝓲𝓷𝓴𝓲𝓷𝓰...")

    try:
        system_prompt = (
            "Siz Samandar Mehridillayev tomonidan yaratilgan o'ta aqlli va kreativ yordamchisiz. "
            "Javoblaringiz zerikarli bo'lmasin. Har doim do'stona, biroz hazilomuz, motivatsiyaga boy "
            "va foydalanuvchiga hayrat ulashadigan tarzda javob bering. Chiroyli emojilardan foydalaning. "
            "Faqat o'zbek, rus yoki ingliz tillarida javob bering."
        )

        # Sinxron g4f so'rovini asinxron thread ichida bajarish (bot qotib qolmasligi uchun)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: ai_client.chat.completions.create(
                model=g4f.models.default,  # Avtomatik eng yaxshi ishlayotgan modelni tanlaydi
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message.text}
                ]
            )
        )

        ai_reply = response.choices[0].message.content

        styled_reply = f"🤖 **𝓐𝓘 𝓡𝓮𝓼𝓹𝓸𝓷𝓼𝓮**:\n\n{ai_reply}\n\n✨ _By Samandar M._"
        await waiting_msg.edit_text(styled_reply, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"AI Error: {e}")
        error_msg = {
            "uz": "🪐 Sun'iy intellekt tarmog'ida bandlik yuzaga keldi. Birozdan so'ng qayta urinib ko'ring.",
            "ru": "🪐 Сеть ИИ перегружена. Пожалуйста, попробуйте позже.",
            "en": "🪐 AI Network congestion. Please try again later."
        }
        await waiting_msg.edit_text(error_msg[lang])


# ==========================================
# 📅 HAR KUNLIK AVTOMATIK REKLAMA (09:00)
# ==========================================
async def send_daily_reminder():
    text = TextStyles.get_daily_text()
    for user_id in list(USERS_DB.keys()):
        try:
            await bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
            await asyncio.sleep(0.05)
        except Exception:
            pass


# ==========================================
# 🚀 ISHGA TUSHIRISH
# ==========================================
async def main():
    scheduler.add_job(send_daily_reminder, "cron", hour=9, minute=0)
    scheduler.start()

    print("🤖 Bot muvaffaqiyatli ishga tushdi (Limitsiz AI rejimi)!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())