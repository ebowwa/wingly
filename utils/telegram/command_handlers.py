import logging
from telegram import Update
from telegram.ext import CallbackContext

class TelegramCommands:
    def __init__(self, user_sessions):
        self.user_sessions = user_sessions

    async def start(self, update: Update, context: CallbackContext):
        """Initiates the tutorial sequence for new users."""
        tutorial_message = (
            "🌟 Let's get to know each other!\n\n"
            "Please say 'Hi' or 'Hello' followed by your full name.\n"
            "For example: 'Hi, I'm John Smith' or 'Hello, my name is Jane Doe'\n\n"
            "This will help me personalize your experience and find better connections for you! ✨"
        )
        await update.message.reply_text(tutorial_message)

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