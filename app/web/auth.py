# app/web/auth.py
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash
from app.config import settings

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    user_hash = settings.USERS.get(username)
    if user_hash and check_password_hash(user_hash, password):
        return username
    return None

@auth.error_handler
def auth_error():
    return "Login required", 401, {"WWW-Authenticate": "Basic realm='Login Required'"}