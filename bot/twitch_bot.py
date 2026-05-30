# bot/twitch_bot.py
import asyncio
import logging
import asqlite
import os
from core.bot import Bot
from database.setup import load_tokens, setup_database
from core.subscriptions import get_subscriptions  # ← Импортируем функцию
from core.config import OWNER_ID, BOT_ID

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS_DB = os.path.join(BASE_DIR, "tokens.db")

logging.basicConfig(level=logging.INFO)

async def main():
    async with asqlite.create_pool(TOKENS_DB) as db_pool:
        # Получаем подписки с правильными ID
        subs = get_subscriptions(owner_id=OWNER_ID, bot_id=BOT_ID)
        
        # Передаём их в бота
        bot = Bot(token_database=db_pool, subscriptions=subs)
        
        await setup_database(db_pool)
        await load_tokens(db_pool, bot.add_token)
        await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("Bot shutting down...")