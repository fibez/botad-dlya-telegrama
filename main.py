import json
import os
import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from datetime import datetime
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CONFIG_FILE_PATH = os.getenv('CONFIG_FILE_PATH')

def load_config(file_path):
    try:
        with open(file_path, 'r') as file:
            config_data = json.load(file)
            return config_data
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

config_data = load_config(CONFIG_FILE_PATH)
CHAT_SETS = fill_chat_sets(config_data)
logger.info(f"Loaded chat sets: {CHAT_SETS}")

async def send_initial_messages(bot: Bot):
    for set_name, chat_set in CHAT_SETS.items():
        chat_id_to_send = chat_set['CHAT_ID_TO_SEND']
        try:
            await bot.send_message(chat_id=chat_id_to_send, text=f"Post in channel {datetime.now()}")
            logger.info(f"Post sent to {set_name}")
        except Exception as e:
            logger.error(f"Failed to send post to {set_name}: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    for set_name, chat_set in CHAT_SETS.items():
        chat_id_to_wait = chat_set['CHAT_ID_TO_WAIT']
        chat_name = chat_set['CHAT_NAME']
        if update.effective_chat.id == int(chat_id_to_wait):
            message_id = update.message.message_id
            try:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Reply in comment section {datetime.now()}", reply_to_message_id=message_id)
                logger.info(f"Replied in {chat_name}")
            except Exception as e:
                logger.error(f"Failed to reply in {chat_name}: {e}")

async def main() -> None:
    application = Application.builder().token(TOKEN).build()
    await send_initial_messages(application.bot)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    await asyncio.sleep(10)

    await application.shutdown()
    await application.stop()
    await application.updater.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
