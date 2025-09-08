import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from agent.agent import graph
from dotenv import load_dotenv


load_dotenv()
# Bot token - set this in your environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Global bot application
bot_app = None


# Bot handlers
async def start(update: Update, context, message):
    await update.message.reply_text("Hello! I'm a  bot with FastAPI.")


async def echo(update: Update, context):
    print(update.message.chat_id)
    response = graph.invoke(
        {"messages": [{"role": "user", "content": update.message.text}]},
        config={"configurable": {"thread_id": update.message.chat_id}},
    )
    final_message = response["messages"][-1]
    await update.message.reply_text(final_message.content)


# Setup bot
async def setup_bot():
    global bot_app
    bot_app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Initialize and start
    await bot_app.initialize()
    await bot_app.start()

    # Set webhook
    await bot_app.bot.set_webhook(WEBHOOK_URL)


async def cleanup_bot():
    global bot_app
    if bot_app:
        await bot_app.bot.delete_webhook()
        await bot_app.stop()
        await bot_app.shutdown()


# FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await setup_bot()
    yield
    # Shutdown
    await cleanup_bot()


# Create FastAPI app
app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming webhook from Telegram"""
    # Get the update data
    update_data = await request.json()
    print("Received update:", update_data)
    # Convert to Update object and process
    update = Update.de_json(update_data, bot_app.bot)
    await bot_app.process_update(update)

    return {"status": "ok"}


@app.get("/setwebhook")
async def set_webhook():
    """Endpoint to set the webhook"""
    if bot_app:
        await bot_app.bot.set_webhook(WEBHOOK_URL)
        return {"status": "webhook set"}
    return {"status": "bot not initialized"}


@app.get("/")
async def root():
    return {"message": "Telegram Bot with FastAPI is running!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
