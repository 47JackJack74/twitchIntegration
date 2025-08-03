import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "super-secret-key")
BOT_SCRIPT = os.getenv("BOT_SCRIPT", "./bot/twitch_bot.py")
HOST = os.getenv("FLASK_HOST", "0.0.0.0")
PORT = int(os.getenv("FLASK_PORT", 5000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://127.0.0.1:5000")

# Аутентификация
USERS = {
    "Jack": "scrypt:32768:8:1$W0fANH0jppjpLItJ$e2d7b32101d9aaf2ab9c372c62195b36e3d64b49fd1369eb7b6f226d13c394224f9d427eec23904e3e2c94c246e53a71736d9178c78187bb67203887f3a1da5b"
}