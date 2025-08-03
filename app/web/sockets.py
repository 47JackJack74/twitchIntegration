# app/web/sockets.py
from flask_socketio import SocketIO, emit

socketio = SocketIO(cors_allowed_origins="*")

# Глобальное состояние квадратов
squares = {}

@socketio.on('connect')
def handle_connect():
    emit('server_message', {'text': 'Connected to WebSocket'})

def broadcast_square(text, start_moving=True):
    squares[text] = True
    socketio.emit('server_message', {'text': text, 'start_moving': start_moving})

def broadcast_delete(text):
    del squares[text]
    socketio.emit('delete_message', {'text': text, 'delete': True})

def broadcast_clear():
    squares.clear()
    socketio.emit('clear_message', {})