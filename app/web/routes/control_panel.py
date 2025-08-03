from flask import render_template, jsonify, request
from app.web.auth import auth
from app.bot.process_manager import start_bot, stop_bot, is_bot_running
from app.web.sockets import broadcast_clear 

def setup_routes(app):
    @app.route('/control_panel')
    @auth.login_required
    def control_panel():
        return render_template('control_panel.html')

    @app.route('/start_bot', methods=['POST'])
    @auth.login_required
    def start_bot_route():
        success, msg = start_bot()
        return jsonify({"status": "started" if success else "failed", "message": msg})

    @app.route('/stop_bot', methods=['POST'])
    @auth.login_required
    def stop_bot_route():
        success, msg = stop_bot()
        broadcast_clear()
        return jsonify({"status": "stopped" if success else "failed", "message": msg})

    @app.route('/bot_status', methods=['GET'])
    @auth.login_required
    def bot_status():
        return jsonify({"status": "running" if is_bot_running() else "stopped"})