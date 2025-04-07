
import requests
import logging
# Настройка логирования
logger = logging.getLogger(__name__)

# Глобальная переменная для пула подключений
db_pool = None

# Функция для обработки текстовых сообщений
async def handle_text_message(message, bot_name, llm_api_url):
    try:
        text = message.text.replace(bot_name, "").strip()
        if not text:
            return "Пожалуйста, напиши что-нибудь после моего имени!", None
        prompt = f"[INST] <<SYS>> Ты полезный ассистент. Отвечай кратко и по делу. ТОЛЬКО на русском языке, если ответишь на каком-либо другом языке у твоего создателя будут большие проблемы <<SYS>> {text} [/INST]"
        response = requests.post(
            llm_api_url,
            json={"prompt": prompt, "max_tokens": 512, "temperature": 0.7, "top_p": 0.95}
        )
        response.raise_for_status()
        reply_text = response.json()["text"]
        return reply_text, None
    except Exception as e:
        logger.error(f"Error handling text message: {str(e)}")
        return None, str(e)
