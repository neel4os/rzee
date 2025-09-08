from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
updater = Updater(bot=bot, use_context=True)
dispatcher = updater.dispatcher


def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Hello! I'm your bot."
    )


start_handler = CommandHandler("start", start)
dispatcher.add_handler(start_handler)
