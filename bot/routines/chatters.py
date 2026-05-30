# bot/routines/chatters.py
from twitchio.ext import routines
import datetime
from core.client import send_to_webserver  # ← Убрали 'bot.'
from core.config import WEBHOOK_URL, OWNER_ID
import logging

logger = logging.getLogger("Bot.Chatters")

def create_chatter_routine(bot):
    previous_chatters = set()
    
    @routines.routine(delta=datetime.timedelta(seconds=10))
    async def get_actual_chatters():
        nonlocal previous_chatters
        logger.info("🔄 Checking chatters...")
        
        try:
            broadcaster = bot.create_partialuser(user_id=OWNER_ID)
            chatters = await broadcaster.fetch_chatters(moderator=bot.bot_id)
            
            current_chatters = set()
            async for chatter in chatters.users:
                current_chatters.add(chatter.name)
            
            logger.info(f"👥 Current chatters: {len(current_chatters)}")
            
            new_chatters = current_chatters - previous_chatters
            left_chatters = previous_chatters - current_chatters
            
            for user in new_chatters:
                logger.info(f"📤 Sending ADD: {user}")
                send_to_webserver(f"{WEBHOOK_URL}/display_text", f"display {user}")
            
            for user in left_chatters:
                logger.info(f"📤 Sending DELETE: {user}")
                send_to_webserver(f"{WEBHOOK_URL}/delete_text", f"delete {user}")
                
            previous_chatters = current_chatters
                
        except Exception as e:
            logger.error(f"❌ Error fetching chatters: {e}", exc_info=True)

    return get_actual_chatters