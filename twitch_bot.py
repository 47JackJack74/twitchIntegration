import asyncio
import datetime
import logging
import sqlite3
import os
import requests
import sys

import threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Flask_test')))
import flask_server # type: ignore

import asqlite
import twitchio
from twitchio.ext import commands, routines
from twitchio import eventsub
from dotenv import load_dotenv


LOGGER: logging.Logger = logging.getLogger("Bot")

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID") # The CLIENT ID from the Twitch Dev Console
CLIENT_SECRET = os.getenv("SECRET") # The CLIENT SECRET from the Twitch Dev Console
BOT_ID = os.getenv("BOT_ID")  # The Account ID of the bot user...
OWNER_ID = os.getenv("OWNER_ID")  # Your personal User ID..
PREFIX = os.getenv("PREFIX")

class Bot(commands.Bot):
    def __init__(self, *, token_database: asqlite.Pool) -> None:
        self.token_database = token_database
        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix=PREFIX,
        )
        def __init__(self):
            self.previous_chatters = set()

    async def setup_hook(self) -> None:
                
        # Add our component which contains our commands...
        await self.add_component(MyComponent(self))

        # Subscribe to read chat (event_message) from our channel as the bot...
        # This creates and opens a websocket to Twitch EventSub...
        subscription = eventsub.ChatMessageSubscription(broadcaster_user_id=OWNER_ID, user_id=BOT_ID)
        await self.subscribe_websocket(payload=subscription)

        # Subscribe and listen to when a stream goes live..
        # For this example listen to our own stream...
        subscription = eventsub.StreamOnlineSubscription(broadcaster_user_id=OWNER_ID)
        await self.subscribe_websocket(payload=subscription)
        
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

    async def load_tokens(self, path: str | None = None) -> None:
        # We don't need to call this manually, it is called in .login() from .start() internally...

        async with self.token_database.acquire() as connection:
            rows: list[sqlite3.Row] = await connection.fetchall("""SELECT * from tokens""")

        for row in rows:
            await self.add_token(row["token"], row["refresh"])

    async def setup_database(self) -> None:
        # Create our token table, if it doesn't exist..
        query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
        async with self.token_database.acquire() as connection:
            await connection.execute(query)

    async def event_ready(self) -> None:
        LOGGER.info("Successfully logged in as: %s", self.bot_id)
        self.get_actual_chatters.start()

    #async def event_stream_online(self) -> None:
    #    self.get_actual_chatters.start()

    async def event_stream_offline(self) -> None:
        self.get_actual_chatters.stop()
    
    async def close(self) -> None:
        await self.clean_webserver()

    async def clean_webserver(self):
        result = call_js_method(command="clear")

    previous_chatters = set()
    
    @routines.routine(delta=datetime.timedelta(seconds=10))
    async def get_actual_chatters(self):
        broadcaster = self.create_partialuser(user_id=OWNER_ID)
        chatters = await broadcaster.fetch_chatters(moderator=BOT_ID)
        #global previous_chatters
        current_chatters = set()
        
        
        async for chatter in chatters.users:
            current_chatters.add(chatter.name)
        
        new_chatters = current_chatters - self.previous_chatters
        left_chatters = self.previous_chatters - current_chatters
        
        self.previous_chatters = current_chatters
        
        result = call_js_method(new_chatters, "display")
        result = call_js_method(left_chatters, "delete")
        

def call_js_method(set_of_users, command):
    if command == "clear":
        url = 'http://127.0.0.1:5000/clear'
        try:
            response = requests.post(url, data=command)  # Отправляем команду в теле запроса
            response.raise_for_status()
            #return response.text #  Возвращаем True при успешном запросе
        except requests.exceptions.RequestException as e:
            print(f"Error during request: {response.status_code}, {response.text}")
            return False
        
    if command == "display":
        url = 'http://127.0.0.1:5000/display_text'
    elif command == "delete":
        url = 'http://127.0.0.1:5000/delete_text'
    for user in set_of_users:
        try:
            response = requests.post(url, data=command + " " + user)  # Отправляем команду в теле запроса
            response.raise_for_status()
            #return response.text #  Возвращаем True при успешном запросе
        except requests.exceptions.RequestException as e:
            print(f"Error during request: {response.status_code}, {response.text}")
            return False

class MyComponent(commands.Component):
    def __init__(self, bot: Bot):
        # Passing args is not required...
        # We pass bot here as an example...
        self.bot = bot
    
    # We use a listener in our Component to display the messages received.
    @commands.Component.listener()
    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        print(f"[{payload.broadcaster.name}] - {payload.chatter.name}: {payload.text}")

    @commands.command(aliases=["hello", "howdy", "hey"])
    async def hi(self, ctx: commands.Context) -> None:
        """Simple command that says hello!

        !hi, !hello, !howdy, !hey
        """
        await ctx.reply(f"Hello {ctx.chatter.mention}!")

    @commands.group(invoke_fallback=True)
    async def socials(self, ctx: commands.Context) -> None:
        """Group command for our social links.

        !socials
        """
        await ctx.send("discord.gg/..., youtube.com/..., twitch.tv/...")

    @socials.command(name="discord")
    async def socials_discord(self, ctx: commands.Context) -> None:
        """Sub command of socials that sends only our discord invite.

        !socials discord
        """
        await ctx.send("discord.gg/...")

    @commands.command(aliases=["repeat"])
    @commands.is_moderator()
    async def say(self, ctx: commands.Context, *, content: str) -> None:
        """Moderator only command which repeats back what you say.

        !say hello world, !repeat I am cool LUL
        """
        await ctx.send(content)

    @commands.Component.listener()
    async def event_stream_online(self, payload: twitchio.StreamOnline) -> None:
        # Event dispatched when a user goes live from the subscription we made above...

        # Keep in mind we are assuming this is for ourselves
        # others may not want your bot randomly sending messages...
        await payload.broadcaster.send_message(
            sender=self.bot.bot_id,
            message=f"Hi... {payload.broadcaster}! You are live!",
        )


def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)

    async def runner() -> None:
        async with asqlite.create_pool("tokens.db") as tdb, Bot(token_database=tdb) as bot:
            await bot.setup_database()
            await bot.start()

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt...")


if __name__ == "__main__":
    main()