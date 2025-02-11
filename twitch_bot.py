from twitchio.ext import commands
from twitchio import Channel, User, Client
import requests
import os
from dotenv import load_dotenv

load_dotenv()
refresh_token = os.getenv("REFRESH_TOKEN")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("SECRET")

def get_new_token():

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(
        "https://id.twitch.tv/oauth2/token", 
        data=data, 
        headers=headers
    )
    
    if response.status_code == 200:
        print(response.json()["access_token"])
        return response.json()["access_token"]
    else:
        print(f"Ошибка получения нового токена: {response.status_code}")
        return None
    
    
def revoke_token(access_token):
    data = {
        "client_id": client_id,
        "token": access_token
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(
        "https://id.twitch.tv/oauth2/revoke", 
        data=data, 
        headers=headers
    )
    
    """
    if response.status_code == 200:
        print(response.json()["access_token"])
        return response.json()["access_token"]
    else:
        print(f"Ошибка получения нового токена: {response.status_code}")
        return None
    """

class Bot(commands.Bot):

    def __init__(self):
        self.token = get_new_token()
        super().__init__(token=self.token, prefix='?', initial_channels=['47jack_jack74'])

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    async def event_message(self, message):
        if message.echo:
            return

        print(message.content)

        await self.handle_commands(message)

    async def event_join(self, channel: Channel, user: User):
        print(user.name)
        await channel.send(f"Ку {user.name}")

    async def event_part(self, user: User):
        print(user.name)
        await user.channel.send(f"ББ {user.name}")

    #???
    async def event_error(self, error, data):
        print(f"Произошла ошибка: {error}, {data}")
        if "401" in str(error):  # Проверяем, является ли ошибка 401 (неавторизовано)
            print("Токен истек, получаем новый...")
            new_token = get_new_token()
            if new_token:
                self.token = new_token
                print("Бот перезапускается с новым токеном")
                self.running = False
                await self.close()
            else:
                print("Ошибка получения нового токена, бот отключен.")
                self.running = False
                await self.close()

    @commands.command(name='привет')
    async def hello(self, ctx: commands.Context):
        revoke_token(self.token)
        ###await ctx.send(f'Hello {ctx.author.name}!')


bot = Bot()
bot.run()