from flask import Flask
from app.web.sockets import socketio
from app.web.routes.control_panel import setup_routes as setup_control_routes
from app.web.routes.widgets import setup_routes as setup_widget_routes
from app.web.routes.api import setup_routes as setup_api_routes
from app.config import settings

def create_app():
    app = Flask(
        __name__,
        static_url_path='/static',
        static_folder='../../static'  # ← относительно app/web/server.py
    )
    app.config['SECRET_KEY'] = settings.SECRET_KEY

    # Подключаем роуты
    setup_control_routes(app)
    setup_widget_routes(app)
    setup_api_routes(app)

    return app

def run_server():
    app = create_app()
    socketio.init_app(app)
    socketio.run(app, host=settings.HOST, port=settings.PORT, debug=True)