import os
import logging
import requests
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# States
SEARCH, API_SETUP = range(2)

# Env variables
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
API_URL = os.environ.get("API_URL", "https://your-universal-api.com/search")
API_KEY = os.environ.get("API_KEY", "YOUR_API_KEY_HERE")


class DataSearchBot:
    def __init__(self):
        self.api_url = API_URL
        self.api_key = API_KEY

    # /start
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome = (
            "👋 Welcome to *OSINT Bot*\n\n"
            "You can search leaked data by:\n"
            "📧 Email / domain\n"
            "👤 Name / Nickname\n"
            "📱 Phone\n"
            "🔑 Password\n"
            "🚗 Car number / VIN\n"
            "✈ Telegram / FB / VK / IG account\n"
            "📍 IP\n\n"
            "📃 You can also send multiple queries (each on a new line).\n\n"
            "🔴 *Credit by Smart Sunny*"
        )
        await update.message.reply_text(welcome, parse_mode="Markdown")

    # /help
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "🤖 **Bot Commands:**\n\n"
            "/start - Start bot\n"
            "/help - Show help\n"
            "/search - Start new search\n"
            "/setapi - Configure API key\n"
            "/cancel - Cancel current operation\n\n"
            "✅ Example searches:\n"
            "`example@gmail.com`\n"
            "`+79002206090`\n"
            "`127.0.0.1`\n"
            "`Petrov Maxim`\n"
            "`O999МУ777`\n"
            "`123qwe`\n\n"
            "📃 Mass Search: send multiple queries, one per line."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    # /search
    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🔍 Please enter your query:\n\n"
            "You can enter email, phone, IP, VIN, username, etc.\n"
            "👉 Multiple queries? Send them line by line."
        )
        return SEARCH

    # Handle entered query
    async def perform_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.message.text.strip()
        await context.bot.send_chat_action(update.effective_chat.id, "typing")
        result = await self.call_universal_api(query)
        await update.message.reply_text(result)
        return ConversationHandler.END

    # Handle normal message (if not in /search flow)
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.message.text.strip()
        await context.bot.send_chat_action(update.effective_chat.id, "typing")
        result = await self.call_universal_api(query)
        await update.message.reply_text(result)

    # /cancel
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❌ Operation cancelled.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # /setapi
    async def setup_api(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Please send your API key:")
        return API_SETUP

    async def save_api_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.api_key = update.message.text.strip()
        await update.message.reply_text("✅ API key updated successfully!")
        return ConversationHandler.END

    # Call external API
    async def call_universal_api(self, query):
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            return "❌ API not configured. Use /setapi."

        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"query": query}
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self.format_api_response(data, query)
            elif response.status_code == 401:
                return "❌ Invalid API key."
            elif response.status_code == 402:
                return "❌ API quota exceeded."
            else:
                return f"❌ API error: {response.status_code}"
        except Exception as e:
            logger.error(f"API error: {e}")
            return "❌ Error contacting API."

    # Format API response
    def format_api_response(self, data, query):
        results = data.get("results", [])
        if not results:
            return f"🔍 No results found for: {query}"

        text = f"🔍 Results for: {query}\n\n"
        for r in results:
            t = r.get("type", "Unknown")
            v = r.get("value", "N/A")
            text += f"📋 Type: {t}\n"
            text += f"🔎 Value: {v}\n"

            details = r.get("details", {})
            if details:
                for k, val in details.items():
                    text += f"  - {k}: {val}\n"

            text += "─" * 30 + "\n\n"

        text += f"📊 Found {len(results)} results.\n\n🔴 *Credit by Smart Sunny*"
        return text


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    bot = DataSearchBot()

    # Conversation handlers
    search_conv = ConversationHandler(
        entry_points=[CommandHandler("search", bot.search)],
        states={SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.perform_search)]},
        fallbacks=[CommandHandler("cancel", bot.cancel)],
    )

    api_conv = ConversationHandler(
        entry_points=[CommandHandler("setapi", bot.setup_api)],
        states={API_SETUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.save_api_key)]},
        fallbacks=[CommandHandler("cancel", bot.cancel)],
    )

    # Handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help))
    application.add_handler(search_conv)
    application.add_handler(api_conv)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))

    # Run bot
    application.run_polling()


if __name__ == "__main__":
    main()
