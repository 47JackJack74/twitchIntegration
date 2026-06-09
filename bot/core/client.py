# bot/core/client.py
import requests
import logging

logger = logging.getLogger("Bot.Client")

def send_to_webserver(endpoint: str, data: str):
    """Отправка данных на веб-сервер"""
    url = endpoint
    logger.info(f"📤 Отправка на {url}: '{data}'")
    
    try:
        # 🔥 Явно указываем Content-Type
        headers = {
            'Content-Type': 'text/plain; charset=utf-8'
        }
        
        response = requests.post(
            url,
            data=data.encode('utf-8'),  # ← Кодируем в UTF-8
            headers=headers,
            timeout=5,
            proxies={"http": None, "https": None}  # 🔥 Игнорируем прокси
        )
        
        logger.info(f"✅ Статус: {response.status_code}")
        logger.info(f"📥 Ответ: {response.text[:100]}")
        
        if response.status_code != 200:
            logger.error(f"❌ Ошибка: {response.status_code} - {response.text}")
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Connection Error: {e}")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout")
        return False
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False