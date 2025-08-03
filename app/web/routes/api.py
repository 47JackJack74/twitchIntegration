# app/web/routes/api.py
from flask import jsonify
from app.web.sockets import squares

def setup_routes(app):
    @app.route('/get_squares', methods=['GET'])
    def get_squares():
        return jsonify(list(squares))