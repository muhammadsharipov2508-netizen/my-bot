import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web
import yt_dlp

TOKEN = "8713206187:AAGqhRBIhYK7r4JUg-QMbr4E6BJ-Alzf0RU"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Веб-сервер барои Render
async def handle(request):
    return web.Response(text="Бот фаъол аст! 🚀")

app = web.Application()
app.router.add_get('/', handle)

user_data = {}

# Забонҳо
LANGUAGES = {
    "ru": {
        "welcome": "Выберите язык / Забонро интихоб кунед:",
        "ask_url": "Отправьте ссылку на видео 📥",
        "loading": "⏳ Загрузка, подождите...",
        "error": "❌ Ошибка при загрузке!",
        "choose": "Что вы хотите получить?",
        "btn_video": "📹 Видео",
        "btn_audio": "🎵 Звук"
    },
    "tj": {
        "welcome": "Салом! Забонро интихоб кунед / Привет! Выберите язык:",
        "ask_url": "Линки видеоро фиристед 📥",
        "loading": "⏳ Боргирӣ шуда истодааст, каме сабр кунед...",
        "error": "❌ Хатогӣ ҳангоми боргирӣ!",
        "choose": "Шумо чиро гирифтан мехоҳед?",
        "btn_video": "📹 Видео",
        "btn_audio": "🎵 Садо"
    }
}

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"),
        types.InlineKeyboardButton("Тоҷикӣ 🇹🇯", callback_data="lang_tj")
    )
    await message.reply(LANGUAGES["tj"]["welcome"], reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('lang_'))
async def process_language(callback_query: types.CallbackQuery):
    lang = callback_query.data.split('_')[1]
    user_data[callback_query.from_user.id] = {"lang": lang}
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, LANGUAGES[lang]["ask_url"])

@dp.message_handler(lambda message: "http" in message.text)
async def ask_action(message: types.Message):
    user_id = message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "tj")
    
    user_data[user_id] = {"lang": lang, "url": message.text}
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(LANGUAGES[lang]["btn_video"], callback_data="get_video"),
        types.InlineKeyboardButton(LANGUAGES[lang]["btn_audio"], callback_data="get_audio")
    )
    await message.reply(LANGUAGES[lang]["choose"], reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data in ["get_video", "get_audio"])
async def process_download(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_data.get(user_id, {})
    lang = data.get("lang", "tj")
    url = data.get("url")
    
    if not url:
        return
        
    await bot.answer_callback_query(callback_query.id)
    status_msg = await bot.send_message(user_id, LANGUAGES[lang]["loading"])
    
    action = callback_query.data
    
    # Танзимоти махсус барои Ютуб ва Инстаграм
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    if action == "get_video":
        ydl_opts['format'] = 'best[ext=mp4]/best'
        ydl_opts['outtmpl'] = f'video_{user_id}.mp4'
    else:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['outtmpl'] = f'audio_{user_id}.mp3'
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        if action == "get_video":
            with open(f'video_{user_id}.mp4', 'rb') as f:
                await bot.send_video(user_id, f)
            os.remove(f'video_{user_id}.mp4')
        else:
            with open(f'audio_{user_id}.mp3', 'rb') as f:
                await bot.send_audio(user_id, f)
            os.remove(f'audio_{user_id}.mp3')
            
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(LANGUAGES[lang]["error"])
        # Тоза кардани файлҳо дар сурати хатогӣ
        for ext in ['mp4', 'mp3']:
            file_path = f'{action.split("_")[1]}_{user_id}.{ext}'
            if os.path.exists(file_path):
                os.remove(file_path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    from threading import Thread
    def run_web():
        web.run_app(app, host='0.0.0.0', port=port)
        
    Thread(target=run_web).start()
    executor.start_polling(dp, skip_updates=True)
