from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Словарь для хранения квадратов
squares = {}

@app.route('/')
def index():
    return render_template('index.html')

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

@socketio.on('connect')
def handle_connect():
    print('Client connected')

if __name__ == '__main__':
    socketio.run(app, debug=True)