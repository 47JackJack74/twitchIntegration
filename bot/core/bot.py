from twitchio.ext import commands
from database.setup import setup_database, load_tokens
from routines.chatters import create_chatter_routine
from events.stream_events import event_ready, event_stream_offline, event_stream_online
from core.config import CLIENT_ID, CLIENT_SECRET, BOT_ID, OWNER_ID, PREFIX
from core.client import send_to_webserver
from core.config import WEBHOOK_URL
import logging
from commands.general import GeneralCommands
from commands.moderation import ModerationCommands

LOGGER = logging.getLogger("Bot")

class Bot(commands.Bot):
    def __init__(self, token_database):
        self.token_database = token_database
        self.previous_chatters = set()
        self.get_actual_chatters = create_chatter_routine(self)

        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix=PREFIX,
        )

    async def setup_hook(self) -> None:
        # Загружаем Cogs
        await self.add_component(GeneralCommands())
        await self.add_component(ModerationCommands())

        # Подписки на EventSub
        from twitchio import eventsub
        subscription = eventsub.ChatMessageSubscription(
            broadcaster_user_id=OWNER_ID,
            user_id=BOT_ID
        )
        await self.subscribe_websocket(payload=subscription)

        subscription = eventsub.StreamOnlineSubscription(broadcaster_user_id=OWNER_ID)
        await self.subscribe_websocket(payload=subscription)

    async def add_token(self, token: str, refresh: str):
        resp = await super().add_token(token, refresh)
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            token = excluded.token,
            refresh = excluded.refresh;
        """
        async with self.token_database.acquire() as conn:
            await conn.execute(query, (resp.user_id, token, refresh))
            await conn.commit()
        LOGGER.info("Token added for user: %s", resp.user_id)
        return resp

    async def event_ready(self):
        await event_ready(self)

    @commands.Component.listener()
    async def event_message(self, message):
        print(f"[{message.broadcaster.name}] {message.chatter.name}: {message.text}")

    @commands.Component.listener()
    async def event_stream_online(self, payload):
        await event_stream_online(self, payload)

    @commands.Component.listener()
    async def event_stream_offline(self, payload):
        await event_stream_offline(self, payload)

    async def close(self):
        send_to_webserver(f"{WEBHOOK_URL}/clear", "clear")
        await super().close()