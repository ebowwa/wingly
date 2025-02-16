import logging
from telegram import Update
from telegram.ext import CallbackContext

class TelegramCommands:
    def __init__(self, user_sessions):
        self.user_sessions = user_sessions

    async def start(self, update: Update, context: CallbackContext):
        """Sends a welcome message when the user starts the bot."""
        welcome_message = (
            "👋 Welcome to Wingly - Your Personal Connection Assistant!\n\n"
            "I'm here to help you build meaningful relationships and find compatible friendships. "
            "You can share voice messages, videos, or text about your interests and experiences.\n\n"
            "Commands:\n"
            "/start - Begin your journey\n"
            "/help - Learn how I can assist you\n"
            "/stop - Pause our conversation\n"
            "/clear - Start fresh\n\n"
            "Let's start building meaningful connections! 🤝"
        )
        await update.message.reply_text(welcome_message)

    async def help(self, update: Update, context: CallbackContext):
        """Shows help information about bot commands and usage."""
        help_text = (
            "🤝 Building Connections with Wingly:\n\n"
            "Commands:\n"
            "/start - Begin your journey\n"
            "/help - See this guide\n"
            "/stop - Take a break\n"
            "/clear - Start fresh\n\n"
            "How I Can Help:\n"
            "🗣 Share voice messages about yourself\n"
            "📹 Send videos about your interests\n"
            "💭 Chat about what you're looking for in friendships\n"
            "🤖 Get personalized insights and connection suggestions\n\n"
            "I'm here to help you find compatible friends and build meaningful relationships! 💫"
        )
        await update.message.reply_text(help_text)

    async def stop(self, update: Update, context: CallbackContext):
        """Stops the current conversation and closes WebSocket connection."""
        user_id = update.message.chat_id
        if user_id in self.user_sessions:
            try:
                await self.user_sessions[user_id].close()
                del self.user_sessions[user_id]
                await update.message.reply_text("Conversation stopped. Send any message to start a new one.")
            except Exception as e:
                logging.error(f"Error stopping conversation: {e}")
                await update.message.reply_text("Error stopping conversation. Please try again.")
        else:
            await update.message.reply_text("No active conversation to stop.")

    async def clear(self, update: Update, context: CallbackContext):
        """Clears the conversation history for the user."""
        user_id = update.message.chat_id
        if user_id in self.user_sessions:
            try:
                await self.user_sessions[user_id].close()
                del self.user_sessions[user_id]
                await update.message.reply_text("Conversation history cleared. You can start a new conversation.")
            except Exception as e:
                logging.error(f"Error clearing conversation: {e}")
                await update.message.reply_text("Error clearing conversation history. Please try again.")
        else:
            await update.message.reply_text("No conversation history to clear.")