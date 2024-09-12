from flask_socketio import emit
from flask import request
from datetime import datetime
import logging
import json

# Set up SocketIO handlers with selective logging
def setup_socketio_handlers(socketio, server, client_frames):
    client_sessions = {}

    @socketio.on('connect')
    def handle_connect():
        # The client should emit the custom session ID after connecting
        logging.getLogger().info(f"Client connected, waiting for session registration...")

    @socketio.on('register_session')
    def handle_register_session(data):
        data = json.loads(data)
        custom_session_id = data['session_id']
        client_sessions[custom_session_id] = {
            'connected_at': datetime.now(),
            'flask_sid': request.sid  # Optionally map the Flask sid to the custom session ID
        }
        print(f"Client registered with custom session ID: {custom_session_id}")
        logging.getLogger().info(f"Client registered with custom session ID: {custom_session_id}")

    @socketio.on('disconnect')
    def handle_disconnect():
        flask_sid = request.sid

        # Find the custom session ID based on Flask's sid
        custom_session_id = None
        for session_id, session_info in client_sessions.items():
            if session_info['flask_sid'] == flask_sid:
                custom_session_id = session_id
                # server.terminate(custom_session_id)

        if custom_session_id:
            del client_sessions[custom_session_id]

            if custom_session_id in client_frames:
                del client_frames[custom_session_id]  # Remove the stored frame

            emit('remove_camera_stream', {'session_id': custom_session_id}, broadcast=True)


