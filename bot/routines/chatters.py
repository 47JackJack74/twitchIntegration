from twitchio.ext import routines
import datetime
from core.client import send_to_webserver
from core.config import WEBHOOK_URL

def create_chatter_routine(bot):
    @routines.routine(delta=datetime.timedelta(seconds=10))
    async def get_actual_chatters():
        broadcaster = bot.create_partialuser(user_id=bot.owner_id)
        try:
            chatters = await broadcaster.fetch_chatters(moderator=bot.bot_id)
            current_chatters = set()

            async for chatter in chatters.users:
                current_chatters.add(chatter.name)

            new_chatters = current_chatters - bot.previous_chatters
            left_chatters = bot.previous_chatters - current_chatters

            bot.previous_chatters = current_chatters

            for user in new_chatters:
                send_to_webserver(f"{WEBHOOK_URL}/display_text", f"display {user}")
            for user in left_chatters:
                send_to_webserver(f"{WEBHOOK_URL}/delete_text", f"delete {user}")

        except Exception as e:
            print(f"Error fetching chatters: {e}")

    return get_actual_chatters