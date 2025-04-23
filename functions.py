import requests
import logging
from collections import deque

# Настройка логирования
logger = logging.getLogger(__name__)

# Глобальная переменная для пула подключений
db_pool = None

# Словарь для хранения истории диалогов: {user_id: deque([(user_message, bot_response), ...])}
DIALOGUE_HISTORY = {}
MAX_HISTORY_LENGTH = 10  # Ограничение на количество сообщений в истории
MAX_PROMPT_LENGTH = 7600  # Максимальная длина промпта в символах (резерв ~548 для системного сообщения и запроса)

# Функция для получения или создания истории пользователя
def get_user_history(user_id):
    if user_id not in DIALOGUE_HISTORY:
        DIALOGUE_HISTORY[user_id] = deque(maxlen=MAX_HISTORY_LENGTH)
    return DIALOGUE_HISTORY[user_id]

# Функция для очистки истории пользователя
def clear_user_history(user_id):
    if user_id in DIALOGUE_HISTORY:
        DIALOGUE_HISTORY[user_id].clear()

# Функция для обрезки истории, чтобы длина промпта не превышала лимит
def trim_history(history, prompt_base, max_length=MAX_PROMPT_LENGTH):
    trimmed_history = deque(history, maxlen=MAX_HISTORY_LENGTH)
    current_prompt = prompt_base
    for user_msg, bot_response in history:
        current_prompt += f"Пользователь: {user_msg}\nАссистент: {bot_response}\n"
    
    # Пока длина промпта превышает максимальную, удаляем самые старые сообщения
    while len(current_prompt) > max_length and trimmed_history:
        trimmed_history.popleft()
        current_prompt = prompt_base
        for user_msg, bot_response in trimmed_history:
            current_prompt += f"Пользователь: {user_msg}\nАссистент: {bot_response}\n"
    
    if len(current_prompt) > max_length:
        logger.warning("Prompt still too long after trimming history, clearing history.")
        trimmed_history.clear()
    
    return trimmed_history

# Функция для обработки текстовых сообщений
async def handle_text_message(message, bot_name, llm_api_url, user_id):
    try:
        text = message.text.replace(bot_name, "").strip().lower()
        if not text:
            return "Пожалуйста, напиши что-нибудь после моего имени!", None

        # Получаем историю пользователя
        history = get_user_history(user_id)

        # Если пользователь написал "предскажи", вызываем генерацию предсказания
        if "предскажи" in text:
            prediction, error = await generate_prediction(llm_api_url, user_id)
            if not error:
                history.append((text, prediction))
            return prediction, error

        # Формируем базовый промпт
        prompt_base = (
            "[INST] <<SYS>> Отвечай кратко, максимально саркастично и максимально токсично, с максимальной порцией ненависти к собеседнику"
            "ТОЛЬКО на русском языке"
            "Учитывай контекст предыдущих сообщений. <<SYS>> "
        )
        # Обрезаем историю, если нужно
        history = trim_history(history, prompt_base)
        
        # Формируем полный промпт с учетом истории
        prompt = prompt_base
        for user_msg, bot_response in history:
            prompt += f"Пользователь: {user_msg}\nАссистент: {bot_response}\n"
        prompt += f"Пользователь: {text}\nАссистент: [/INST]"

        # Отправляем запрос к LLM
        response = requests.post(
            llm_api_url,
            json={"prompt": prompt, "max_tokens": 512, "temperature": 0.7, "top_p": 0.95}
        )
        response.raise_for_status()
        reply_text = response.json()["text"].strip()

        # Сохраняем сообщение и ответ в историю
        history.append((text, reply_text))

        return reply_text, None
    except Exception as e:
        logger.error(f"Error handling text message: {str(e)}")
        return None, str(e)

# Функция для генерации предсказания
async def generate_prediction(llm_api_url, user_id):
    try:
        # Получаем историю пользователя
        history = get_user_history(user_id)

        # Формируем базовый промпт для предсказания
        prompt_base = (
            "[INST] <<SYS>> Ты астролог, который делает короткие и креативные предсказания на день. "
            "Предсказание должно быть на русском языке, в одно предложение, максимально саркастичным, максимально токсичным" 
            "максимально глупым, максимально едким"
            "Будь оригинальным и не используй другие языки! <<SYS>> Сделай предсказание на сегодня. [/INST]"
        )
        # Обрезаем историю, если нужно
        history = trim_history(history, prompt_base)
        
        # Формируем полный промпт
        prompt = prompt_base
        for user_msg, bot_response in history:
            prompt += f"Пользователь: {user_msg}\nАссистент: {bot_response}\n"
        prompt += "Сделай предсказание на сегодня. [/INST]"

        response = requests.post(
            llm_api_url,
            json={"prompt": prompt, "max_tokens": 200, "temperature": 0.9, "top_p": 0.95}
        )
        response.raise_for_status()
        prediction = response.json()["text"].strip()

        # Сохраняем предсказание в историю
        history.append(("предскажи", prediction))

        return prediction, None
    except Exception as e:
        logger.error(f"Error generating prediction: {str(e)}")
        return None, str(e)


        

        