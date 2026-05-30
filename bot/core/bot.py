import twitchio
from twitchio.ext import commands
from twitchio import eventsub
from database.setup import setup_database, load_tokens
from routines.chatters import create_chatter_routine
from events.stream_events import event_ready, event_stream_offline, event_stream_online
from core.config import CLIENT_ID, CLIENT_SECRET, BOT_ID, OWNER_ID, PREFIX
from core.client import send_to_webserver
from core.config import WEBHOOK_URL
import logging
import asqlite
from commands.general import GeneralCommands
from commands.moderation import ModerationCommands
from core.subscriptions import get_subscriptions  # ← Импортируем функцию

LOGGER = logging.getLogger("Bot")

class Bot(commands.Bot):
    def __init__(
        self, 
        *, 
        token_database: asqlite.Pool, 
        subscriptions: list[eventsub.SubscriptionPayload] | None = None
    ) -> None:
        self.token_database = token_database
        self.previous_chatters = set()
        self.get_actual_chatters = create_chatter_routine(self)

        # Если подписки не переданы — создаём дефолтные с реальными ID
        if subscriptions is None:
            subscriptions = get_subscriptions(owner_id=OWNER_ID, bot_id=BOT_ID)

        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix=PREFIX,
            subscriptions=subscriptions,
            force_subscribe=True,
        )

    async def setup_hook(self) -> None:
        # Загружаем Cogs
        await self.add_component(GeneralCommands())
        await self.add_component(ModerationCommands())

    async def event_oauth_authorized(self, payload: twitchio.authentication.UserTokenPayload) -> None:
        await self.add_token(payload.access_token, payload.refresh_token)

        if not payload.user_id:
            return

        if payload.user_id == self.bot_id:
            # We usually don't want subscribe to events on the bots channel...
            return

        # A list of subscriptions we would like to make to the newly authorized channel...
        subs: list[eventsub.SubscriptionPayload] = [
            eventsub.ChatMessageSubscription(broadcaster_user_id=payload.user_id, user_id=self.bot_id),
        ]

        resp: twitchio.MultiSubscribePayload = await self.multi_subscribe(subs)
        if resp.errors:
            LOGGER.warning("Failed to subscribe to: %r, for user: %s", resp.errors, payload.user_id)

    async def add_token(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        # Make sure to call super() as it will add the tokens interally and return us some data...
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(token, refresh)

        # Store our tokens in a simple SQLite Database when they are authorized...
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            token = excluded.token,
            refresh = excluded.refresh;
        """

        async with self.token_database.acquire() as connection:
            await connection.execute(query, (resp.user_id, token, refresh))

        LOGGER.info("Added token to the database for user: %s", resp.user_id)
        return resp

    async def event_ready(self) -> None:
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