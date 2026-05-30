# app/web/server.py
import os
from flask import Flask
from app.web.sockets import socketio
from app.web.routes.control_panel import setup_routes as setup_control_routes
from app.web.routes.widgets import setup_routes as setup_widget_routes
from app.web.routes.api import setup_routes as setup_api_routes
from app.web.routes.oauth import bp as oauth_bp  # ← Импортируем Blueprint
from app.config import settings

def create_app():
    # Вычисляем абсолютный путь к статике (надёжнее относительных путей)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    STATIC_DIR = os.path.join(BASE_DIR, 'static')
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

    app = Flask(
        __name__,
        static_url_path='/static',
        static_folder=STATIC_DIR,
        template_folder=TEMPLATE_DIR
    )
    
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['SESSION_COOKIE_SECURE'] = False  # True для HTTPS в продакшене
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # 🔹 Регистрируем ВСЕ роуты и Blueprint'ы
    setup_control_routes(app)
    setup_widget_routes(app)
    setup_api_routes(app)
    
    app.register_blueprint(oauth_bp)

    # 🔹 Обработчики ошибок (опционально, но полезно)
    @app.errorhandler(404)
    def not_found(e):
        return "Страница не найдена", 404

    @app.errorhandler(500)
    def server_error(e):
        return "Внутренняя ошибка сервера", 500

    return app

def run_server():
    app = create_app()
    
    # Инициализируем SocketIO ПОСЛЕ создания app и регистрации всех роутов
    socketio.init_app(
        app,
        cors_allowed_origins="*",           # Разрешаем все источники
        async_mode='threading',             # Используем threading (проще для начала)
        ping_timeout=60,                    # Увеличиваем таймаут
        ping_interval=25,                   # Интервал ping
        logger=False,                       # Отключаем логи Socket.IO (шумные)
        engineio_logger=False,              # Отключаем логи Engine.IO
        always_connect=True,                # Разрешаем подключения
    )
    
    # SSL сертификаты от Let's Encrypt
    ssl_cert = '/etc/letsencrypt/live/twitchbot.duckdns.org/fullchain.pem'
    ssl_key = '/etc/letsencrypt/live/twitchbot.duckdns.org/privkey.pem'
    
    # Запуск сервера
    """
    socketio.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        debug=True,
        allow_unsafe_werkzeug=True
    )
    """
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        ssl_context=(ssl_cert, ssl_key),  # ← Включаем HTTPS
        debug=False,  # ← Выключи debug в продакшене!
        allow_unsafe_werkzeug=True
    )