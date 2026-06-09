# app/web/sockets.py
from flask_socketio import SocketIO

# 🔥 Создаём socketio (НО не инициализируем здесь)
socketio = SocketIO(cors_allowed_origins="*")

# Глобальное состояние квадратов
squares = {}

def broadcast_square(text, start_moving=True):
    squares[text] = True
    # 🔥 Используем socketio.emit() (метод экземпляра)
    socketio.emit('server_message', {'text': text, 'start_moving': start_moving})

def broadcast_delete(text):
    if text in squares:
        del squares[text]
    socketio.emit('delete_message', {'text': text, 'delete': True})

def broadcast_clear():
    squares.clear()
    socketio.emit('clear_message', {})

def get_squares():
    return list(squares.keys())