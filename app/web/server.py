# app/web/server.py
import os
from flask import Flask
import sqlite3
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
    
    # 🔽 ВСТАВИТЬ ЭТОТ БЛОК ПЕРЕД return app
    db_path = os.getenv("DATABASE_PATH", "/app/db/tokens.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                user_id TEXT PRIMARY KEY,
                token TEXT NOT NULL,
                refresh TEXT NOT NULL,
                widget_token TEXT UNIQUE  --  НОВОЕ ПОЛЕ
            )
        """)
        conn.commit()
        print("✅ DB table 'tokens' ready")
    
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

    socketio.init_app(app, async_mode='threading', cors_allowed_origins="*")

    return app

def run_server():
    app = create_app()
    
    port = int(os.getenv("FLASK_PORT", 5000))
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    
    print(f" Starting waitress on {host}:{port}")
    
    from waitress import serve
    serve(app, host=host, port=port, threads=8)
    
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