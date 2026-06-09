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
import threading
import time
import signal
import sys

def watchdog():
    """Перезапускает процесс, если сервер не отвечает 3 минуты"""
    import requests
    
    last_ok = time.time()
    check_interval = 30
    timeout = 120
    
    # 🔥 Ждём старта сервера
    print("⏳ Watchdog: waiting for server to start (60s)...")
    time.sleep(60)
    
    # Определяем URL
    use_ssl = os.getenv("USE_SSL", "false").lower() == "true"
    port = int(os.getenv("FLASK_PORT", 5000))
    scheme = "https" if use_ssl else "http"
    url = f'{scheme}://localhost:{port}/'
    
    print(f"🔍 Watchdog started, checking {url} every {check_interval}s")
    
    while True:
        try:
            time.sleep(check_interval)
            
            # 🔥 Используем requests вместо urllib
            response = requests.get(
                url, 
                timeout=10,
                verify=False  # Игнорируем SSL сертификат
            )
            
            if response.status_code < 500:
                last_ok = time.time()
                
        except Exception as e:
            elapsed = time.time() - last_ok
            print(f"⚠️ Watchdog: {e}, elapsed: {elapsed:.0f}s")
            
            if elapsed > timeout:
                print(f"🛑 Server unresponsive for {elapsed:.0f}s! Restarting...")
                os.kill(os.getpid(), signal.SIGKILL)
                sys.exit(1)

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

    socketio.init_app(app, async_mode='eventlet', cors_allowed_origins="*")

    return app

def run_server():
    app = create_app()
    
    watchdog_thread = threading.Thread(target=watchdog, daemon=True)
    watchdog_thread.start()
    
    port = int(os.getenv("FLASK_PORT", 5000))
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    
    use_ssl = os.getenv("USE_SSL", "false").lower() == "true"
    ssl_cert = os.getenv("SSL_CERT_PATH")
    ssl_key = os.getenv("SSL_KEY_PATH")
    
    print(f"🚀 Starting Eventlet server on {host}:{port}")
    
    # Проверяем SSL
    ssl_enabled = False
    if use_ssl and ssl_cert and ssl_key:
        if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
            ssl_enabled = True
            print(f"✅ SSL enabled: {ssl_cert}")
        else:
            print(f"⚠️ SSL files not found at {ssl_cert} / {ssl_key}")
    
    if ssl_enabled:
        # 🔥 С SSL: создаём SSL-сокет вручную
        import eventlet
        import eventlet.wsgi
        
        sock = eventlet.listen((host, port))
        sock = eventlet.wrap_ssl(
            sock,
            certfile=ssl_cert,
            keyfile=ssl_key,
            server_side=True
        )
        
        eventlet.wsgi.server(sock, app)
    else:
        # 🔥 Без SSL: используем socketio.run()
        socketio.run(
            app,
            host=host,
            port=port,
            debug=False,           
            use_reloader=False,
        )
    
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