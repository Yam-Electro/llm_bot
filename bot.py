import asyncio
import sys
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.enums import ParseMode, UpdateType
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
import logging
import functions as f

# Добавляем отладочный вывод для проверки путей
print("Current working directory:", os.getcwd())
print("sys.path:", sys.path)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = "@pobazekat_bot"
LLM_API_URL = "http://llm_back:8844/generate"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message((F.text.startswith(BOT_NAME)) | (F.reply_to_message.from_user.id == bot.id))
async def handle_text(message: Message):
    reply_text, error = await f.handle_text_message(message, BOT_NAME, LLM_API_URL)
    if error:
        clean_error = str(error).split(':')[0]  # Берем только начало ошибки
        await message.reply(f"Произошла ошибка: {clean_error}", parse_mode=ParseMode.HTML)
    else:
        await message.reply(reply_text, parse_mode=ParseMode.HTML)

@dp.message(Command("start"))
async def send_welcome(message: Message):

    await message.answer(f"Привет! Я могу:\n"
        f"- Отвечать на текстовые сообщения, если упомянуть меня: {BOT_NAME}\n",
        parse_mode=ParseMode.HTML
    )

async def main():
    # Указываем типы обновлений, которые бот должен обрабатывать
    allowed_updates = [
        UpdateType.MESSAGE,
        UpdateType.CALLBACK_QUERY,
        UpdateType.CHAT_MEMBER
    ]
    await dp.start_polling(bot, allowed_updates=allowed_updates)

if __name__ == '__main__':
    asyncio.run(main())