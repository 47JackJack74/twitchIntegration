from flask import render_template, request, jsonify
import re
from app.web.sockets import broadcast_square, broadcast_delete, broadcast_clear

def setup_routes(app):
    @app.route('/widget_viewers')
    def widget_panel():
        return render_template('widget_viewers.html')

    @app.route('/display_text', methods=['POST'])
    def display_text():
        data = request.get_data(as_text=True)
        match = re.match(r'display\s+(.+)', data)
        if match:
            text = match.group(1)
            broadcast_square(text)
            return 'Square added', 200
        return 'Invalid command', 400

    @app.route('/delete_text', methods=['POST'])
    def delete_text():
        data = request.get_data(as_text=True)
        match = re.match(r'delete\s+(.+)', data)
        if match:
            text = match.group(1)
            broadcast_delete(text)
            return 'Square removed', 200
        return 'Invalid command', 400

    @app.route('/clear', methods=['POST'])
    def clear_squares():
        broadcast_clear()
        return 'Cleared', 200