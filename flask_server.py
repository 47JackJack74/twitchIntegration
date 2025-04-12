from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import re
import os
import subprocess
import threading

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Словарь для хранения квадратов
squares = {}

# Глобальная переменная для хранения процесса бота
bot_process = None

# Маршрут для панели управления ботом
@app.route('/control_panel')
def control_panel():
    return render_template('control_panel.html')

# Маршрут для включения бота
@app.route('/start_bot', methods=['POST'])
def start_bot():
    global bot_process
    if not bot_process:  # Запускаем бота только если он не запущен
        bot_process = subprocess.Popen([os.sys.executable, 'twitch_bot.py'])
        return jsonify({"status": "started"})
    return jsonify({"status": "already_running"})

# Маршрут для выключения бота
@app.route('/stop_bot', methods=['POST'])
def stop_bot():
    global bot_process
    if bot_process:  # Останавливаем бота только если он запущен
        perform_clear()
        bot_process.terminate()
        bot_process = None
        return jsonify({"status": "stopped"})
    return jsonify({"status": "already_stopped"})

# Маршрут для панели виджетов
@app.route('/widget_viewers')
def widget_panel():
    return render_template('widget_viewers.html')

@app.route('/display_text', methods=['POST'])
def display_text():
    data = request.get_data(as_text=True)
    match = re.match(r'display\s+(.*)', data)
    if match:
        text = match.group(1)
        squares[text] = True # Квадрат добавился
        socketio.emit('server_message', {'text': text, 'start_moving': True})
        return 'Квадрат добавлен', 200
    else:
        return 'Неверная команда', 400

@app.route('/delete_text', methods=['POST'])
def delete_text():
    data = request.get_data(as_text=True)
    match = re.match(r'delete\s+(.*)', data)
    if match:
        text = match.group(1)
        if text in squares:
            del squares[text] # Квадрат удалился
            socketio.emit('delete_message', {'text': text, 'delete':True})
            return 'Квадрат удален', 200
        else:
            return f"Квадрат с текстом \"{text}\" не найден.", 404
    else:
      return 'Неверная команда', 400
    
# Общая функция для очистки
def perform_clear():
    """Очищает все квадраты."""
    squares.clear()  # Очищаем словарь с квадратами
    socketio.emit('clear_message', {})  # Отправляем сообщение о очистке
    return 'Вебсервер очищен', 200

# Маршрут для получения текущего состояния squares
@app.route('/get_squares', methods=['GET'])
def get_squares():
    """Возвращает текущее состояние словаря squares."""
    return jsonify(list(squares.keys()))

@socketio.on('connect')
def handle_connect():
    print('Client connected')

def run_server():
    app.run()

if __name__ == '__main__':
    socketio.run(app, debug=True)