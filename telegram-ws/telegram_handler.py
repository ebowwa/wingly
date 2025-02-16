import asyncio
import json
import logging
import websockets
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
WS_URL = "ws://localhost:8080/api/conversation"

# Store user WebSocket sessions
user_sessions = {}


async def handle_private_message(update: Update, context):
    """Handles direct messages from users and sends them to the WebSocket server."""
    user_id = update.message.chat_id
    
    if update.message.voice:
        try:
            voice_file = await update.message.voice.get_file()
            file_path = f"voice_message_{user_id}.ogg"
            await voice_file.download_to_drive(file_path)
            logging.info(f"Voice message downloaded to {file_path}")
            await update.message.reply_text("Voice message received, processing...")
            return
        except Exception as e:
            logging.error(f"Failed to download voice message: {e}")
            await update.message.reply_text("Sorry, I couldn't process your voice message.")
            return
    
    message_text = update.message.text

    logging.info(f"Received message from user {user_id}: {message_text}")

    # If user does not have an active WebSocket session, create one
    if user_id not in user_sessions:
        try:
            websocket = await websockets.connect(WS_URL)
            user_sessions[user_id] = websocket
            logging.info(f"WebSocket connection established for user {user_id}")
        except Exception as e:
            logging.error(f"Failed to connect to WebSocket: {e}")
            await update.message.reply_text("Error connecting to the conversation service.")
            return

    websocket = user_sessions[user_id]

    try:
        # Send user message to WebSocket
        await websocket.send(message_text)
        logging.info(f"Sent message to WebSocket: {message_text}")

        # Wait for WebSocket response
        response = await websocket.recv()
        logging.info(f"Received response from WebSocket: {response}")

        # Try parsing JSON response if available
        try:
            parsed_response = json.loads(response)
            formatted_response = json.dumps(parsed_response, indent=2)
            await update.message.reply_text(f"Summary:\n{formatted_response}")
            del user_sessions[user_id]  # End session
        except json.JSONDecodeError:
            await update.message.reply_text(response)

    except Exception as e:
        logging.error(f"Error in WebSocket communication: {e}")
        await update.message.reply_text("An error occurred while processing your request.")


async def start(update: Update, context):
    """Sends a welcome message when the user starts the bot."""
    await update.message.reply_text("Welcome! Send me a message, and I will process it.")


def main():
    """Start the bot."""
    app = Application.builder().token(TOKEN).build()
    
    # Update handlers to include voice messages
    app.add_handler(MessageHandler(filters.Command("start"), start))
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.VOICE) & filters.ChatType.PRIVATE, 
        handle_private_message
    ))
    
    logging.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
