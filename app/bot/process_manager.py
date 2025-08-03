# app/bot/process_manager.py
import subprocess
import sys
import os
from app.config import settings

_bot_process = None

def start_bot():
    global _bot_process
    if _bot_process is None:
        script_path = os.path.abspath(settings.BOT_SCRIPT)
        if not os.path.exists(script_path):
            return False, f"Script not found: {script_path}"
        _bot_process = subprocess.Popen(
            [sys.executable, "twitch_bot.py"],
            cwd = os.path.abspath(os.path.join(script_path, '..')),  # ← Ключевой момент: cwd внутри папки bot/
            env = {**os.environ}  # можно передать переменные окружения
        )
        return True, "Bot started"
    return False, "Bot already running"

def stop_bot():
    global _bot_process
    if _bot_process is not None:
        _bot_process.terminate()
        _bot_process.wait(timeout=5)
        _bot_process = None
        return True, "Bot stopped"
    return False, "Bot not running"

def is_bot_running():
    global _bot_process
    return _bot_process is not None and _bot_process.poll() is None