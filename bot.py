import logging
from datetime import time, timezone
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio
from config import BOT_TOKEN
from db import init_db, get_user_coins, add_coin_to_user, remove_coin_from_user, initialize_user_defaults, get_all_user_chats
from api import get_prices

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_COINS = ["SOL", "ETH", "BTC", "BNB"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start: Initialize user with defaults."""
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "Unknown"
    initialize_user_defaults(chat_id, username)
    await update.message.reply_text("Welcome! You've been added default coins. Use /help for commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help."""
    help_text = """
Commands:
/course - Get current prices of your coins
/add <coin_name> - Add a coin using coin's tag (like USDT, SOL etc.) (e.g., /add USDT)
/list - List your coins
/delete <coin_name> - Remove a coin (e.g., /delete USDT)
/help - Show this help
    """
    await update.message.reply_text(help_text)

async def course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /course: Send prices."""
    chat_id = update.effective_chat.id
    coins = get_user_coins(chat_id)
    if not coins:
        await update.message.reply_text("No coins in your list.")
        return
    
    prices = get_prices(coins)
    message = "Current prices:\n"
    for coin in coins:
        price = prices.get(coin, 0)
        formatted_price = f"{price:,.4f}".replace(",", " ").replace(".", ",")
        message += f"{coin} - $ {formatted_price}\n"
    
    await update.message.reply_text(message)

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add <coin_name>."""
    if not context.args:
        await update.message.reply_text("Usage: /add <coin_name> (e.g., /add USDT)")
        return
    
    coin_name = ' '.join(context.args).strip().upper()
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "Unknown"
    
    added = add_coin_to_user(chat_id, username, coin_name)
    if added:
        await update.message.reply_text(f"Added {coin_name} to your list.")
    else:
        await update.message.reply_text(f"{coin_name} is already in your list.")

async def list_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list: Show coins without prices."""
    chat_id = update.effective_chat.id
    coins = get_user_coins(chat_id)
    if not coins:
        await update.message.reply_text("No coins in your list.")
        return
    
    message = "Your coins:\n" + '\n'.join(coins)
    await update.message.reply_text(message)

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delete <coin_name>."""
    if not context.args:
        await update.message.reply_text("Usage: /delete <coin_name> (e.g., /delete USDT)")
        return
    
    coin_name = ' '.join(context.args).strip().upper()
    chat_id = update.effective_chat.id
    
    removed = remove_coin_from_user(chat_id, coin_name)
    if removed:
        await update.message.reply_text(f"Removed {coin_name} from your list.")
    else:
        await update.message.reply_text(f"{coin_name} not found in your list.")

async def daily_broadcast(context: ContextTypes.DEFAULT_TYPE):
    """Daily job: Send prices to all users at 00:00 UTC."""
    users = get_all_user_chats()
    for chat_id, username in users:
        coins = get_user_coins(chat_id)
        prices = get_prices(coins)
        message = f"Good morning, {username}! Current prices:\n"
        for coin in coins:
            price = prices.get(coin, 0)
            formatted_price = f"{price:,.4f}".replace(",", " ").replace(".", ",")
            message += f"{coin} - $ {formatted_price}\n"
        
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.error(f"Failed to send to {chat_id}: {e}")

def main():
    """Start the bot."""
    init_db()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("course", course))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("list", list_coins))
    application.add_handler(CommandHandler("delete", delete))
    
    # Daily job at 00:00 UTC (7:00 local? But specified UTC 00:00)
    job_queue = application.job_queue
    job_queue.run_daily(daily_broadcast, time=time(7, 0, 0, tzinfo=timezone.utc))
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
