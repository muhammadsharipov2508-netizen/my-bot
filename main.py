import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web
import yt_dlp
from pyshazam import Shazam

# ТОКЕНИ БОТИ ХУДРО ДАР ИН ҶО ГУЗОРЕД
TOKEN = "8713206187:AAGqhRBIhYK7r4JUg-QMbr4E6BJ-Alzf0RU"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Веб-сервер барои Render
async def handle(request):
    return web.Response(text="Бот фаъол аст! 🚀")

app = web.Application()
app.router.add_get('/', handle)

user_data = {}

LANGUAGES = {
    "ru": {
        "welcome": "Выберите язык / Забонро интихоб кунед:",
        "ask_url": "Отправьте ссылку на видео 📥",
        "loading": "⏳ Загрузка, подождите...",
        "error": "❌ Ошибка!",
        "choose": "Что вы хотите сделать?",
        "btn_video": "📹 Видео",
        "btn_audio": "🎵 Звук",
        "btn_shazam": "🔍 Найти песню (Shazam)",
        "ask_voice": "Отправьте голосовое сообщение (Голос) с песней 🎤",
        "found": "🎶 Найдена песня: **{title}**\n👤 Исполнитель: {artist}\n\n⏳ Ищу саму песню в YouTube..."
    },
    "tj": {
        "welcome": "Салом! Забонро интихоб кунед / Привет! Выберите язык:",
        "ask_url": "Линки видеоро фиристед 📥",
        "loading": "⏳ Боргирӣ шуда истодааст, каме сабр кунед...",
        "error": "❌ Хатогӣ рӯй дод!",
        "choose": "Шумо чиро гирифтан мехоҳед?",
        "btn_video": "📹 Видео",
        "btn_audio": "🎵 Садо",
        "btn_shazam": "🔍 Ёфтани суруд (Shazam)",
        "ask_voice": "Паёми овозӣ (Голос)-ро бо суруд фиристед 🎤",
        "found": "🎶 Суруд ёфт шуд: **{title}**\n👤 Овозхон: {artist}\n\n⏳ Худи мусиқиро аз YouTube кофта истодаам..."
    }
}

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru"),
            types.InlineKeyboardButton(text="Тоҷикӣ 🇹🇯", callback_data="lang_tj")
        ]
    ])
    await message.reply(LANGUAGES["tj"]["welcome"], reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('lang_'))
async def process_language(callback_query: types.CallbackQuery):
    lang = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id] = {"lang": lang}
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, LANGUAGES[lang]["ask_url"])

@dp.message(lambda message: message.text and "http" in message.text)
async def ask_action(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "tj")
    
    user_data[user_id] = {"lang": lang, "url": message.text}
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text=LANGUAGES[lang]["btn_video"], callback_data="get_video"),
            types.InlineKeyboardButton(text=LANGUAGES[lang]["btn_audio"], callback_data="get_audio")
        ],
        [
            types.InlineKeyboardButton(text=LANGUAGES[lang]["btn_shazam"], callback_data="get_shazam")
        ]
    ])
    await message.reply(LANGUAGES[lang]["choose"], reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "get_shazam")
async def ask_for_voice(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "tj")
    await callback_query.answer()
    await bot.send_message(user_id, LANGUAGES[lang]["ask_voice"])

# Қабули овоз ва ёфтани он тавассути pyshazam
@dp.message(lambda message: message.voice)
async def process_voice(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "tj")
    
    status_msg = await message.reply(LANGUAGES[lang]["loading"])
    
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    
    voice_path = f"voice_{user_id}.ogg"
    await bot.download_file(file_path, voice_path)
    
    try:
        # Истифодаи китобхонаи нав барои шинохтан
        shazam = Shazam(voice_path)
        recognize_generator = shazam.recognize()
        out = next(recognize_generator, None)
        
        if not out or not out[1].get('track'):
            await status_msg.edit_text("❌ Шазам сурудро нашинохт.")
            os.remove(voice_path)
            return
            
        track_info = out[1]['track']
        title = track_info['title']
        artist = track_info['subtitle']
        
        await status_msg.edit_text(LANGUAGES[lang]["found"].format(title=title, artist=artist), parse_mode="Markdown")
        
        # Ҷустуҷӯ ва боргирии худи мусиқӣ аз Ютуб
        search_query = f"ytsearch:{artist} {title}"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'song_{user_id}.mp3',
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [search_query])
            
        # Фиристодани файл
        audio_file = types.FSInputFile(f'song_{user_id}.mp3')
        await bot.send_audio(user_id, audio_file, title=title, performer=artist)
        
        # Тоза кардани файлҳо
        os.remove(voice_path)
        os.remove(f'song_{user_id}.mp3')
        await bot.delete_message(user_id, status_msg.message_id)
        
    except Exception as e:
        await bot.edit_message_text(LANGUAGES[lang]["error"], user_id, status_msg.message_id)
        if os.path.exists(voice_path): os.remove(voice_path)
        if os.path.exists(f'song_{user_id}.mp3'): os.remove(f'song_{user_id}.mp3')

# Боргирии оддии видеову аудио
@dp.callback_query(lambda c: c.data in ["get_video", "get_audio"])
async def process_download(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_data.get(user_id, {})
    lang = data.get("lang", "tj")
    url = data.get("url")
    
    if not url: return
        
    await callback_query.answer()
    status_msg = await bot.send_message(user_id, LANGUAGES[lang]["loading"])
    
    action = callback_query.data
    ydl_opts = {'quiet': True, 'no_warnings': True}
    
    if action == "get_video":
        ydl_opts['format'] = 'best[ext=mp4]/best'
        ydl_opts['outtmpl'] = f'video_{user_id}.mp4'
    else:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['outtmpl'] = f'audio_{user_id}.mp3'
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])
            
        if action == "get_video":
            video_file = types.FSInputFile(f'video_{user_id}.mp4')
            await bot.send_video(user_id, video_file)
            os.remove(f'video_{user_id}.mp4')
        else:
            audio_file = types.FSInputFile(f'audio_{user_id}.mp3')
            await bot.send_audio(user_id, audio_file)
            os.remove(f'audio_{user_id}.mp3')
            
        await bot.delete_message(user_id, status_msg.message_id)
        
    except Exception as e:
        await bot.edit_message_text(LANGUAGES[lang]["error"], user_id, status_msg.message_id)
        for ext in ['mp4', 'mp3']:
            file_path = f'{action.split("_")[1]}_{user_id}.{ext}'
            if os.path.exists(file_path): os.remove(file_path)

async def main():
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
