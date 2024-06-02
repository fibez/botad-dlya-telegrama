from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import asyncio
import json
# import logging
import os

# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CONFIG_FILE_PATH = os.getenv('CONFIG_FILE_PATH')


def load_config(file_path):
    try:
        with open(file_path, 'r') as file:
            config_data = json.load(file)
            return config_data
    except FileNotFoundError:
        print(f"Config file '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error parsing JSON in config file '{file_path}'.")
        return None
    
def fill_chat_sets(config_data):
    chat_sets = {}
    if config_data and 'channels' in config_data:
        for channel in config_data['channels']:
            channel_name = channel['name']
            chat_id_to_send = str(channel['id'])
            chat_id_to_wait = str(channel['chat']['chat_id'])
            chat_sets[channel_name] = {'CHAT_ID_TO_SEND': chat_id_to_send, 'CHAT_ID_TO_WAIT': chat_id_to_wait}
    return chat_sets


config_data = load_config(CONFIG_FILE_PATH)
CHAT_SETS = fill_chat_sets(config_data)

async def send_initial_messages(bot: Bot):
    for set_name, chat_set in CHAT_SETS.items():
        chat_id_to_send = chat_set['CHAT_ID_TO_SEND']
        await bot.send_message(chat_id=chat_id_to_send, text=f"123Initial message for {set_name}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    for set_name, chat_set in CHAT_SETS.items():
        chat_id_to_wait = chat_set['CHAT_ID_TO_WAIT']
        if update.effective_chat.id == int(chat_id_to_wait):
            message_id = update.message.message_id
            print(f"Received message in {set_name}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="123Reply message.", reply_to_message_id=message_id)
            print(f"Replied in {set_name}")

async def main() -> None:
    application = Application.builder().token(TOKEN).build()

    await send_initial_messages(application.bot)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await application.initialize()
    await application.start()
    print("Bot is running...")
    await application.updater.start_polling()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()