from core.client import send_to_webserver
from core.config import WEBHOOK_URL

async def event_ready(bot):
    print(f"Bot logged in as {bot.bot_id}")
    bot.get_actual_chatters.start()

async def event_stream_offline(bot, payload):
    bot.get_actual_chatters.stop()

async def event_stream_online(bot, payload):
    await payload.broadcaster.send_message(
        sender=bot.bot_id,
        message=f"Hi... {payload.broadcaster}! You are live!"
    )