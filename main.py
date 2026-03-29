import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

# ⚠️ Токени боти худро дар ин ҷо гузоред
TOKEN = "8713206187:AAGqhRBIhYK7r4JUg-QMbr4E6BJ-Alzf0RU"

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

LANG_TEXTS = {
    "ru": {
        "welcome": "Привет! Выберите язык / Салом! Забонро интихоб кунед:",
        "ask_url": "Отправьте ссылку на видео 🔗",
        "choose_action": "Что вы хотите получить?",
        "btn_video": "🎥 Видео",
        "btn_voice": "🔊 Звук видео",
        "loading": "⏳ Загрузка, подождите...",
        "error": "❌ Произошла ошибка! Линк кор накард.",
        "invalid_url": "⚠️ Пожалуйста, отправьте правильную ссылку!",
    },
    "en": {
        "welcome": "Hello! Choose a language / Салом! Забонро интихоб кунед:",
        "ask_url": "Send me a video link 🔗",
        "choose_action": "What do you want to get?",
        "btn_video": "🎥 Video",
        "btn_voice": "🔊 Video Audio",
        "loading": "⏳ Downloading, please wait...",
        "error": "❌ An error occurred! Link failed.",
        "invalid_url": "⚠️ Please send a valid link!",
    },
    "fa": {
        "welcome": "سلام! زبان را انتخاب کنید / Салом! Забонро интихоб кунед:",
        "ask_url": "لینک ویدیو را بفرستید 🔗",
        "choose_action": "چه چیزی می‌خواهید دریافت کنید؟",
        "btn_video": "🎥 ویدیو",
        "btn_voice": "🔊 صدای ویدیو",
        "loading": "⏳ در حال دانلود, لطفا صبر کنید...",
        "error": "❌ خطایی رخ داد! لینک کار نکرد.",
        "invalid_url": "⚠️ لطفا یک لینک معتبر بفرستید!",
    },
}

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru"))
    builder.add(InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en"))
    builder.add(InlineKeyboardButton(text="فارسی 🇮🇷", callback_data="lang_fa"))
    await message.answer(LANG_TEXTS["en"]["welcome"], reply_markup=builder.as_markup())

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_data[callback.from_user.id] = {"lang": lang}
    await callback.message.edit_text(LANG_TEXTS[lang]["ask_url"])
    await callback.answer()

@dp.message()
async def handle_url(message: types.Message):
    user_id = message.from_user.id
    url = message.text
    lang = user_data.get(user_id, {}).get("lang", "en")

    if not url.startswith(("http://", "https://")):
        await message.answer(LANG_TEXTS[lang]["invalid_url"])
        return

    user_data[user_id] = {"lang": lang, "url": url}

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=LANG_TEXTS[lang]["btn_video"], callback_data="act_video"))
    builder.add(InlineKeyboardButton(text=LANG_TEXTS[lang]["btn_voice"], callback_data="act_voice"))

    await message.answer(LANG_TEXTS[lang]["choose_action"], reply_markup=builder.as_markup())

@dp.callback_query(lambda c: c.data.startswith("act_"))
async def process_action(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.split("_")[1]

    if user_id not in user_data or "url" not in user_data[user_id]:
        await callback.answer()
        return

    lang = user_data[user_id]["lang"]
    url = user_data[user_id]["url"]

    msg = await callback.message.edit_text(LANG_TEXTS[lang]["loading"])
    file_template = f"file_{callback.message.message_id}.%(ext)s"
    filename = None

    # Танзимоти махсус барои фиреб додани Инстаграм
    base_opts = {
        "outtmpl": file_template,
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {"instagram": {"ig_sig_key_version": [None]}}
    }

    try:
        if action == "act_voice":
            base_opts["format"] = "bestaudio/best"
            chat_action = "upload_voice"
        else:
            base_opts["format"] = "best[ext=mp4]/best"
            chat_action = "upload_video"

        with yt_dlp.YoutubeDL(base_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if filename and os.path.exists(filename):
            await bot.send_chat_action(callback.message.chat.id, chat_action)
            file_to_send = FSInputFile(filename)
            
            if action == "act_voice":
                await callback.message.answer_audio(audio=file_to_send)
            else:
                await callback.message.answer_video(video=file_to_send)
                
            await msg.delete()
        else:
            await msg.edit_text(LANG_TEXTS[lang]["error"])

    except Exception as e:
        print(f"Хатогӣ: {e}")
        await msg.edit_text(LANG_TEXTS[lang]["error"])
    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
