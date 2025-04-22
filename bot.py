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

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = "@pobazekat_bot"
LLM_API_URL = "http://llm_back:8844/generate"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Обработчик текстовых сообщений с упоминанием бота или ответом
@dp.message((F.text.startswith(BOT_NAME)) | (F.reply_to_message.from_user.id == bot.id))
async def handle_text(message: Message):
    user_id = message.from_user.id
    reply_text, error = await f.handle_text_message(message, BOT_NAME, LLM_API_URL, user_id)
    if error:
        clean_error = str(error).split(':')[0]
        await message.reply(f"Произошла ошибка: {clean_error}", parse_mode=ParseMode.HTML)
    else:
        await message.reply(reply_text, parse_mode=ParseMode.HTML)

# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer(
        f"Привет! Я могу:\n"
        f"- Отвечать на текстовые сообщения, если упомянуть меня: {BOT_NAME}\n"
        f"- Делать предсказания на день: используй /predict или напиши '{BOT_NAME} предскажи'\n"
        f"- Запоминать наш разговор и отвечать в контексте\n"
        f"- Сбросить историю беседы: /clear\n",
        parse_mode=ParseMode.HTML
    )

# Обработчик команды /predict или текста "предскажи"
@dp.message(Command("predict"))
async def send_prediction(message: Message):
    user_id = message.from_user.id
    prediction, error = await f.generate_prediction(LLM_API_URL, user_id)
    if error:
        clean_error = str(error).split(':')[0]
        await message.reply(f"Произошла ошибка: {clean_error}", parse_mode=ParseMode.HTML)
    else:
        await message.reply(prediction, parse_mode=ParseMode.HTML)

# Обработчик команды /clear для сброса истории
@dp.message(Command("clear"))
async def clear_history(message: Message):
    user_id = message.from_user.id
    f.clear_user_history(user_id)
    await message.reply("История беседы очищена!", parse_mode=ParseMode.HTML)

async def main():
    allowed_updates = [
        UpdateType.MESSAGE,
        UpdateType.CALLBACK_QUERY,
        UpdateType.CHAT_MEMBER
    ]
    await dp.start_polling(bot, allowed_updates=allowed_updates)

if __name__ == '__main__':
    asyncio.run(main())