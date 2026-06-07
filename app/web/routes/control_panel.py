# app/web/routes/control_panel.py
from flask import render_template, jsonify, request, session, redirect, url_for
from app.web.auth import auth  # Оставляем для админки, если нужно
from app.bot.process_manager import start_bot, stop_bot, is_bot_running
from app.web.sockets import broadcast_clear 

def setup_routes(app):
    
    # 🔹 1. Главная страница: редирект на вход или в панель
    @app.route('/')
    def index():
        if 'twitch_user' in session:
            return redirect(url_for('control_panel'))
        return redirect(url_for('oauth.login'))  # Ссылка на роут в oauth.py

    # 🔹 2. Панель управления (теперь без @auth.login_required)
    @app.route('/control_panel')
    def control_panel():
        # Проверяем, авторизован ли пользователь через Twitch
        user = session.get('twitch_user')
        if not user:
            return redirect(url_for('oauth.login'))
        
        # Передаём данные пользователя и статус бота в шаблон
        return render_template(
            'control_panel.html', 
            user=user,  # {'id': '...', 'login': '...'}
            bot_status="running" if is_bot_running() else "stopped"
        )

    # 🔹 3. Запуск бота (доступен только авторизованным)
    @app.route('/start_bot', methods=['POST'])
    def start_bot_route():
        if 'twitch_user' not in session:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
            
        success, msg = start_bot()
        return jsonify({
            "status": "started" if success else "failed", 
            "message": msg
        })

    # 🔹 4. Остановка бота + очистка виджета
    @app.route('/stop_bot', methods=['POST'])
    def stop_bot_route():
        if 'twitch_user' not in session:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
            
        success, msg = stop_bot()
        if success:
            broadcast_clear()  # Очищаем квадраты на виджете
        return jsonify({
            "status": "stopped" if success else "failed", 
            "message": msg
        })

    # 🔹 5. Статус бота (для AJAX-опросов)
    @app.route('/bot_status', methods=['GET'])
    def bot_status():
        # Можно оставить публичным или требовать сессию
        return jsonify({"status": "running" if is_bot_running() else "stopped"})

    # 🔹 6. Выход из аккаунта
    @app.route('/logout')
    def logout():
        session.pop('twitch_user', None)
        return redirect(url_for('index'))