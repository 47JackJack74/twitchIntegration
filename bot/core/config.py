import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("SECRET")
BOT_ID = os.getenv("BOT_ID")
OWNER_ID = os.getenv("OWNER_ID")
PREFIX = os.getenv("PREFIX")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://127.0.0.1:5000")