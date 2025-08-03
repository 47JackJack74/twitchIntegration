import asyncio
import logging
import asqlite
import os
from core.bot import Bot
from database.setup import load_tokens, setup_database

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # → TwitchBot/
TOKENS_DB = os.path.join(BASE_DIR, "tokens.db")

logging.basicConfig(level=logging.INFO)

async def main():
    async with asqlite.create_pool(TOKENS_DB) as db_pool:
        bot = Bot(token_database=db_pool)
        await setup_database(db_pool)
        await load_tokens(db_pool, bot.add_token)
        await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("Bot shutting down...")