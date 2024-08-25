from flask import request, jsonify
from functools import wraps
from datetime import datetime

# Global variable to track the last activity time
last_activity_time = datetime.now()

def register_update_routes(app, server):

    @app.route('/settings', methods=['POST'])
    def update_settings():
        """
        Update the server settings based on the JSON payload received in the request.
        """
        new_config = request.json
        if new_config:
            server.update_config(new_config)
            return jsonify({
                "place": server.config["location"]["place"],
                "building": server.config["location"]["building"],
                "floor": server.config["location"]["floor"],
                "scale": server.config["location"]["scale"]
            }), 200
        else:
            return jsonify({'error': 'No configuration data provided'}), 400

    @app.route('/start', methods=['POST'])
    @update_last_activity
    def start_server():
        """
        Start the server. The server object should have a method to handle this.
        """
        try:
            server.start()
            return jsonify({'status': 'Server started successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/terminate', methods=['POST'])
    @update_last_activity
    def terminate_server():
        """
        Terminate the server. The server object should have a method to handle this.
        """
        try:
            server.terminate()
            return jsonify({'status': 'Server terminated successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Decorator to update last activity timestamp
def update_last_activity(f):
    """
    Decorator to update the last activity time every time a route is accessed.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        global last_activity_time
        last_activity_time = datetime.now()
        return f(*args, **kwargs)
    return decorated_function
