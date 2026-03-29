import os
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web
import yt_dlp

TOKEN = "8713206187:AAGqhRBIhYK7r4JUg-QMbr4E6BJ-Alzf0RU"
AUDD_API = "f764d26d4143e8cb0affca6f6f91e96a"  # ← аз audd.io гир

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ========= WEB SERVER =========
async def handle(request):
    return web.Response(text="Bot is running 🚀")

app = web.Application()
app.router.add_get('/', handle)

# ========= MEMORY =========
user_data = {}

# ========= LANG =========
LANG = {
    "tj": {
        "welcome": "Салом! Забонро интихоб кунед:",
        "ask": "Линк фиристед 📥",
        "choose": "Чиро мехоҳед?",
        "video": "📹 Видео",
        "audio": "🎵 Садо",
        "find": "🎧 Ёфтани мусиқӣ",
        "loading": "⏳ Интизор шавед...",
        "error": "❌ Хатогӣ!",
        "not_found": "❌ Мусиқӣ ёфт нашуд"
    }
}

# ========= START =========
@dp.message(Command("start"))
async def start(msg: types.Message):
    user_data[msg.from_user.id] = {"lang": "tj"}
    await msg.answer(LANG["tj"]["ask"])

# ========= URL =========
@dp.message(lambda m: m.text and "http" in m.text)
async def get_url(msg: types.Message):
    uid = msg.from_user.id
    user_data[uid]["url"] = msg.text

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text=LANG["tj"]["video"], callback_data="video"),
            types.InlineKeyboardButton(text=LANG["tj"]["audio"], callback_data="audio")
        ],
        [
            types.InlineKeyboardButton(text=LANG["tj"]["find"], callback_data="find")
        ]
    ])

    await msg.answer(LANG["tj"]["choose"], reply_markup=kb)

# ========= DOWNLOAD =========
async def download_media(url, filename, fmt):
    ydl_opts = {
        'format': fmt,
        'outtmpl': filename,
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        await asyncio.to_thread(ydl.download, [url])

# ========= VIDEO / AUDIO =========
@dp.callback_query(lambda c: c.data in ["video", "audio"])
async def handle_download(call: types.CallbackQuery):
    uid = call.from_user.id
    url = user_data.get(uid, {}).get("url")

    if not url:
        return

    await call.answer()
    msg = await bot.send_message(uid, LANG["tj"]["loading"])

    try:
        if call.data == "video":
            file = f"video_{uid}.mp4"
            await download_media(url, file, "best[ext=mp4]/best")
            await bot.send_video(uid, types.FSInputFile(file))

        else:
            file = f"audio_{uid}.mp3"
            await download_media(url, file, "bestaudio/best")
            await bot.send_audio(uid, types.FSInputFile(file))

        os.remove(file)
        await bot.delete_message(uid, msg.message_id)

    except:
        await bot.edit_message_text(LANG["tj"]["error"], uid, msg.message_id)

# ========= FIND MUSIC =========
@dp.callback_query(lambda c: c.data == "find")
async def find_music(call: types.CallbackQuery):
    uid = call.from_user.id
    url = user_data.get(uid, {}).get("url")

    await call.answer()
    msg = await bot.send_message(uid, "🎧 Ҷустуҷӯ...")

    try:
        file = f"music_{uid}.mp3"

        # download audio
        await download_media(url, file, "bestaudio/best")

        # send to AudD
        with open(file, 'rb') as f:
            r = requests.post(
                "https://api.audd.io/",
                data={"api_token": AUDD_API},
                files={"file": f}
            )

        data = r.json()

        if data.get("result"):
            title = data["result"]["title"]
            artist = data["result"]["artist"]

            await bot.send_message(uid, f"🎵 {title}\n👤 {artist}")
        else:
            await bot.send_message(uid, LANG["tj"]["not_found"])

        os.remove(file)
        await bot.delete_message(uid, msg.message_id)

    except Exception as e:
        await bot.send_message(uid, LANG["tj"]["error"])

# ========= RUN =========
async def main():
    port = int(os.environ.get("PORT", 10000))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())