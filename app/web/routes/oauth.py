# app/web/routes/oauth.py
import os
import requests
import sqlite3
from flask import Blueprint, request, redirect, session, jsonify, current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.config import settings

bp = Blueprint('oauth', __name__, url_prefix='/oauth')

# 🔐 Временный секрет для авторизации бота (УДАЛИТЬ ПОСЛЕ ПЕРВОГО ИСПОЛЬЗОВАНИЯ!)
ADMIN_SECRET = "change_this_later_123"

# 📋 Скоупы для разных ролей
SCOPES = {
    "streamer": "channel:bot chat:read chat:edit moderation:read channel:manage:broadcast",
    "bot": "user:read:chat user:write:chat user:bot"
}

# 🔗 URI для редиректа
REDIRECT_URI = f"{settings.WEBHOOK_URL}/oauth/callback"

# 🗄 Путь к базе данных
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = os.path.join(BASE_DIR, "tokens.db")


@bp.route('/login')
def login():
    """1. Генерирует ссылку на авторизацию Twitch с криптографическим state"""
    
    #  Временный хак для бота
    if request.args.get('admin_bot') == ADMIN_SECRET:
        role = 'bot'
    else:
        role = request.args.get('role', 'streamer')
    
    if role not in SCOPES:
        role = 'streamer'
    
    scopes = SCOPES[role]
    
    # 🔐 Stateless State: подписываем роль секретным ключом приложения
    # itsdangerous уже установлен как зависимость Flask
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    state_token = serializer.dumps({'role': role})
    
    print(f"🔍 WEBHOOK_URL from env: {settings.WEBHOOK_URL}")
    print(f"🔍 REDIRECT_URI: {REDIRECT_URI}")
    
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize"
        f"?client_id={settings.CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={scopes}"
        f"&state={state_token}"
        f"&force_verify=true"
    )
    
    return redirect(auth_url)


@bp.route('/callback')
def callback():
    """2. Принимает код, проверяет подпись state, сохраняет токен"""
    code = request.args.get('code')
    state_param = request.args.get('state')
    
    if not code:
        return jsonify({'error': 'No authorization code provided'}), 400
    
    if not state_param:
        return jsonify({'error': 'Missing state parameter'}), 400

    # 🔐 Проверяем и расшифровываем state
    try:
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        # state валиден только 300 секунд (5 минут) — защита от replay-атак
        data = serializer.loads(state_param, max_age=300)
        role = data.get('role', 'streamer')
    except SignatureExpired:
        return jsonify({'error': 'State token expired. Please try again.'}), 400
    except BadSignature:
        return jsonify({'error': 'Invalid state signature. Possible tampering.'}), 400

    # 🔁 Обмен кода на токены
    token_resp = requests.post('https://id.twitch.tv/oauth2/token', data={
        'client_id': settings.CLIENT_ID,
        'client_secret': settings.CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
    })

    if token_resp.status_code != 200:
        return jsonify({
            'error': 'Token exchange failed', 
            'details': token_resp.text
        }), 500

    token_data = token_resp.json()
    access_token = token_data['access_token']
    refresh_token = token_data['refresh_token']

    # 👤 Получаем данные пользователя
    user_resp = requests.get(
        'https://api.twitch.tv/helix/users', 
        headers={
            'Authorization': f'Bearer {access_token}',  # ✅ ПРАВИЛЬНО
            'Client-ID': settings.CLIENT_ID,
        }
    )
    
    # 🔍 DEBUG: покажи ответ от Twitch API
    print("=" * 50)
    print("🔍 TWITCH API RESPONSE:")
    print(f"Status Code: {user_resp.status_code}")
    print(f"Response Body: {user_resp.text}")
    print(f"Request Headers: Authorization=OAuth ***{access_token[-4:]}, Client-ID={settings.CLIENT_ID}")
    print("=" * 50)
    
    if user_resp.status_code != 200:
        return jsonify({'error': 'Failed to fetch user info'}), 500
        
    user_info = user_resp.json()['data'][0]
    user_id = user_info['id']
    login = user_info['login']

    # 💾 Сохраняем в tokens.db
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO tokens (user_id, token, refresh)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    token = excluded.token,
                    refresh = excluded.refresh
            """, (user_id, access_token, refresh_token))
            conn.commit()
    except sqlite3.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    #  Сохраняем в сессию только для UI (не влияет на OAuth)
    session['twitch_user'] = {
        'id': user_id, 
        'login': login,
        'role': role
    }
    
    return redirect('/control_panel')


@bp.route('/logout')
def logout():
    session.pop('twitch_user', None)
    return redirect('/')