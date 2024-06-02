import json
import os
import logging
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from datetime import datetime
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Токен вашего бота и пути к конфигурационным файлам
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CONFIG_FILE_PATH = os.getenv('CONFIG_FILE_PATH')
MESSAGES_CONFIG_FILE_PATH = os.getenv('MESSAGES_CONFIG_FILE_PATH')

# Состояние для отслеживания отправленных сообщений
sent_messages = {}

def load_config(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"Config file '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        logger.error(f"Error parsing JSON in config file '{file_path}'.")
        return None

def fill_chat_sets(config_data):
    chat_sets = {}
    if config_data and 'channels' in config_data:
        for channel in config_data['channels']:
            channel_name = channel['name']
            chat_id_to_send = str(channel['id'])
            chat_id_to_wait = str(channel['chat']['chat_id'])
            chat_name = channel['chat']['chat_name']
            chat_sets[channel_name] = {
                'CHAT_ID_TO_SEND': chat_id_to_send,
                'CHAT_ID_TO_WAIT': chat_id_to_wait,
                'CHAT_NAME': chat_name
            }
    return chat_sets

# Загрузка и парсинг конфигурационных файлов
config_data = load_config(CONFIG_FILE_PATH)
messages_config = load_config(MESSAGES_CONFIG_FILE_PATH)
CHAT_SETS = fill_chat_sets(config_data)
logger.info(f"Loaded chat sets: {CHAT_SETS}")

async def send_initial_messages(bot: Bot):
    for set_name, chat_set in CHAT_SETS.items():
        chat_id_to_send = chat_set['CHAT_ID_TO_SEND']
        message = await bot.send_photo(chat_id=chat_id_to_send, photo=messages_config['post_image_path'], caption=f"{messages_config['post_text']} \n\n {datetime.now()}")
        sent_messages[chat_set['CHAT_ID_TO_WAIT']] = message.message_id
        logger.info(f"Post sent to {set_name} with message_id: {message.message_id}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = str(update.effective_chat.id)
    message_id = update.message.message_id
    chat_name = None

    # Найти название чата по chat_id
    for set_name, chat_set in CHAT_SETS.items():
        if chat_set['CHAT_ID_TO_WAIT'] == chat_id:
            chat_name = chat_set['CHAT_NAME']
            break

    logger.info(f"Received message with ID: {message_id} in chat '{chat_name}' with chat ID: {chat_id}")

    
    for msg in messages_config["chat_messages"]:
        reply_image_path = msg.get("reply_image_path")
        if reply_image_path:
            await context.bot.send_photo(chat_id=chat_id, photo=reply_image_path, caption=f"{msg['reply_text']} \n\n{datetime.now()}", reply_to_message_id=message_id)
            logger.info(f"Photo reply with caption was sent to chat {chat_id}")
        else: 
            await context.bot.send_message(chat_id=chat_id, text=f"{msg['reply_text']} \n\n {datetime.now()}", reply_to_message_id=message_id)
            logger.info(f"Reply was sent to chat {chat_id}")



    



async def main() -> None:
    application = Application.builder().token(TOKEN).build()
    await send_initial_messages(application.bot)
    application.add_handler(MessageHandler(filters.CAPTION & ~filters.COMMAND, handle_message))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Ожидаем завершения всех задач
    await asyncio.sleep(60)  # Увеличено время ожидания для тестирования

    await application.shutdown()
    await application.stop()
    await application.updater.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
