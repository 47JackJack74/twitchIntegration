# app/bot/process_manager.py
import subprocess
import sys
import os
import psutil
from app.config import settings
import threading

_bot_process = None

def start_bot():
    global _bot_process
    if _bot_process is not None and _bot_process.poll() is None:
        return False, "Bot already running"

    # Получаем путь из настроек
    bot_path_setting = getattr(settings, 'BOT_SCRIPT_DIR', None) or getattr(settings, 'BOT_SCRIPT', None)
    
    if not bot_path_setting:
        # Фолбэк: вычисляем путь относительно этого файла
        bot_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'bot'))
    else:
        bot_path = os.path.abspath(bot_path_setting)

    # 🔍 Проверяем: это файл или папка?
    if os.path.isfile(bot_path):
        # Если указан файл напрямую
        bot_script = bot_path
        bot_dir = os.path.dirname(bot_path)
    elif os.path.isdir(bot_path):
        # Если указана папка
        bot_script = os.path.join(bot_path, "twitch_bot.py")
        bot_dir = bot_path
    else:
        return False, f"Path not found: {bot_path}"

    if not os.path.exists(bot_script):
        return False, f"Script not found: {bot_script}"

    try:
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        
        _bot_process = subprocess.Popen(
            [sys.executable, "twitch_bot.py"],
            cwd=bot_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=creationflags
        )
        def stream_output():
            for line in _bot_process.stdout:
                print(f"[BOT] {line}", end='', flush=True)
        
        threading.Thread(target=stream_output, daemon=True).start()
        
        print(f"✅ Bot started with PID: {_bot_process.pid}")
        return True, "Bot started"
    except Exception as e:
        return False, f"Failed to start bot: {e}"

def stop_bot():
    global _bot_process
    if _bot_process is None:
        return False, "Bot not running"

    pid = _bot_process.pid
    try:
        # 1️⃣ Сначала пробуем мягкое завершение (даём боту 3 секунды на очистку)
        _bot_process.terminate()
        try:
            _bot_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            print(f"️ Process {pid} didn't respond, force killing...")

        # 2️⃣ Принудительно убиваем всё дерево процессов (основной + дочерние)
        try:
            parent = psutil.Process(pid)
            # recursive=True находит и убивает ВСЕ дочерние процессы
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass  # Процесс уже мёртв

        # 3️⃣ Ждём полного освобождения ресурсов
        _bot_process.wait(timeout=2)
        _bot_process = None
        return True, "Bot stopped"
        
    except Exception as e:
        return False, f"Error stopping bot: {e}"

def is_bot_running():
    global _bot_process
    return _bot_process is not None and _bot_process.poll() is None