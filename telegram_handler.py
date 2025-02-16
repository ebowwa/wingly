import asyncio
import json
import logging
import websockets
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
import os
from utils.ai.gemini_process import process_with_gemini
from utils.ai.process_llm_request import ProcessLLMRequestContent
from utils.telegram.command_handlers import TelegramCommands

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
WS_URL = "ws://localhost:8080/api/conversation"

# Store user WebSocket sessions
user_sessions = {}

# Downloading and Processing of Content including Text should occur alongside these downloading functions
# recieved inputs can be either hardcoded reasoning flow and parameters or otherwise webhooks to process the content using the handle_private_message to return the wanted results
async def download_voice_message(update: Update, user_id: int) -> tuple[bool, str]:
    """Downloads a voice message from a Telegram update."""
    try:
        voice_file = await update.message.voice.get_file()
        file_path = f"voice_message_{user_id}.ogg"
        await voice_file.download_to_drive(file_path)
        logging.info(f"Voice message downloaded to {file_path}")
        return True, file_path
    except Exception as e:
        error_msg = f"Failed to download voice message: {e}"
        logging.error(error_msg)
        return False, error_msg

async def download_video_message(update: Update, user_id: int) -> tuple[bool, str]:
    """
    Downloads a video message from a Telegram update.
    
    Args:
        update: The telegram update containing the video message
        user_id: The user's telegram ID
        
    Returns:
        tuple: (success: bool, result: str)
        - If successful: (True, file_path)
        - If failed: (False, error_message)
    """
    try:
        video_file = await update.message.video.get_file()
        file_path = f"video_message_{user_id}.mp4"
        await video_file.download_to_drive(file_path)
        logging.info(f"Video message downloaded to {file_path}")
        return True, file_path
    except Exception as e:
        error_msg = f"Failed to download video message: {e}"
        logging.error(error_msg)
        return False, error_msg

# Update the message handler to include video
async def process_downloaded_file(file_path: str, mime_type: str) -> tuple[bool, str]:
    """Process a downloaded file with Gemini without modifying the original download logic."""
    try:
        # Create the request structure directly instead of using ProcessLLMRequestContent
        with open(file_path, 'rb') as f:
            file_data = f.read()
            
        uploaded_files = {
            "role": "user",
            "content": {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": file_data
                        }
                    },
                    {
                        "text": "Analyzing media content"
                    }
                ]
            }
        }
        
        result = process_with_gemini(
            uploaded_files=uploaded_files,
            prompt_type="default_transcription",
            temperature=0.7,
            max_output_tokens=4096
        )
        return True, json.dumps(result, indent=2)
    except Exception as e:
        return False, str(e)

# Modify only the message handling part in handle_private_message
async def format_response_for_telegram(response: str, response_type: str = "default") -> str:
    """
    Format any type of response for Telegram output.
    
    Args:
        response: Raw response string (usually JSON)
        response_type: Type of response ('gemini', 'websocket', 'default', etc.)
    
    Returns:
        str: Formatted message ready for Telegram
    """
    try:
        # Try to parse JSON if available
        data = json.loads(response) if isinstance(response, str) else response
        
        if not isinstance(data, (dict, list)):
            return str(data)
        
        # Format based on response type
        if response_type == "gemini":
            return f"Analysis complete:\n{json.dumps(data, indent=2)}"
        elif response_type == "websocket":
            return f"Summary:\n{json.dumps(data, indent=2)}"
        else:
            return json.dumps(data, indent=2)
            
    except json.JSONDecodeError:
        # Return raw response if not JSON
        return str(response)
    except Exception as e:
        logging.error(f"Error formatting response: {e}")
        return f"Error formatting response: {str(e)}"

# Update handle_private_message to use the new formatter
async def handle_private_message(update: Update, context):
    user_id = update.message.chat_id
    
    if update.message.voice:
        success, file_path = await download_voice_message(update, user_id)
        if not success:
            await update.message.reply_text("Sorry, I couldn't process your voice message.")
            return
            
        success, result = await process_downloaded_file(file_path, "audio/ogg")
        if success:
            formatted_result = await format_response_for_telegram(result, "gemini")
            await update.message.reply_text(formatted_result)
        else:
            await update.message.reply_text(f"Processing failed: {result}")
        return
        
    elif update.message.video:
        success, file_path = await download_video_message(update, user_id)
        if not success:
            await update.message.reply_text("Sorry, I couldn't process your video message.")
            return
            
        # Process the downloaded file
        success, result = await process_downloaded_file(file_path, "video/mp4")
        if success:
            await update.message.reply_text(f"Analysis complete:\n{result}")
        else:
            await update.message.reply_text(f"Processing failed: {result}")
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    app = Application.builder().token(TOKEN).build()
    
    # Initialize command handlers
    commands = TelegramCommands(user_sessions)
    
    # Add command handlers
    app.add_handler(CommandHandler("start", commands.start))
    app.add_handler(CommandHandler("help", commands.help))
    app.add_handler(CommandHandler("stop", commands.stop))
    app.add_handler(CommandHandler("clear", commands.clear))
    
    # Add message handler
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.VOICE | filters.VIDEO) & filters.ChatType.PRIVATE, 
        handle_private_message
    ))
    
    logging.info("Bot is running...")
    app.run_polling()
