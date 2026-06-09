import os
from pathlib import Path

# 🔥 2. Загружаем .env ДО всех остальных импортов
from dotenv import load_dotenv
load_dotenv()

# 🔥 3. Определяем корень проекта и путь к БД
PROJECT_ROOT = Path(__file__).resolve().parent
db_path = os.getenv("DATABASE_PATH", "tokens.db")
os.environ["DATABASE_PATH"] = str(PROJECT_ROOT / db_path)

print(f"✅ DATABASE_PATH: {os.environ['DATABASE_PATH']}")

# 🔥 4. Только ПОСЛЕ load_dotenv() импортируем свой код
from app.config import settings
from app.web.server import run_server

if __name__ == "__main__":
    print(f"✅ CLIENT_ID: {settings.CLIENT_ID}")
    run_server()