from flask import request, jsonify, send_file
from PIL import Image
import io
import base64
import os
import time
import cv2

from utils.cache_manager import CacheManager

# This dictionary is used to store frames associated with client sessions
client_frames = {}
# This dictionary is used to track localization states
localization_states = {}
# This dictionary acts as a simple cache for map segments
map_cache = {}

# Configuration for localization retries and timeouts
COARSE_LOCALIZE_THRESHOLD = 5  # Number of failures before doing a coarse localize
TIMEOUT_SECONDS = 20  # Time since the last successful localize before doing a coarse localize

def register_frame_routes(app, server, socketio):
    @app.route('/stream_frame', methods=['POST'])
    def stream_frame():
        data = request.json
        frame_base64 = data.get('frame')
        session_id = data.get('session_id')
        do_localize = data.get('do_localize', False)

        if frame_base64 and session_id:
            frame_data = base64.b64decode(frame_base64.split(',')[1]) if ',' in frame_base64 else base64.b64decode(frame_base64)
            frame = Image.open(io.BytesIO(frame_data))

            # Convert to RGB format
            r, g, b = frame.split()
            frame = Image.merge("RGB", (b, g, r))
            
            if frame is not None:
                client_frames[session_id] = frame
                response_data = {'status': 'frame received'}

                # Perform localization if requested
                if do_localize:
                    pose = server.handle_localization(session_id, frame)
                    response_data['pose'] = pose

                buffered = io.BytesIO()
                frame.save(buffered, format="JPEG")
                new_frame_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                response_data['frame'] = new_frame_base64
                socketio.emit('camera_frame', {'session_id': session_id, 'frame': new_frame_base64})
                return jsonify(response_data), 200
            else:
                return jsonify({'error': 'Failed to process frame'}), 500
        else:
            return jsonify({'error': 'No frame provided or session_id missing'}), 400

    @app.route('/list_clients', methods=['GET'])
    def list_clients():
        """
        List all clients who have sent frames.
        """
        return jsonify(list(client_frames.keys()))

    @app.route('/get_frame/<client_id>', methods=['GET'])
    def get_frame(client_id):
        """
        Retrieve the last frame sent by a specific client.
        """
        frame = client_frames.get(client_id)
        if frame is not None:
            buffered = io.BytesIO()
            frame.save(buffered, format="JPEG")
            buffered.seek(0)
            return send_file(buffered, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'No frame available for this client'}), 404

    @app.route('/get_image/<id>/<image_name>', methods=['GET'])
    def get_image(id, image_name):
        """
        Retrieve a specific image associated with a session and image name.
        """
        image_path = os.path.join(server.root, 'logs', server.config['location']['place'], server.config['location']['building'], server.config['location']['floor'], id, 'images', image_name)
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({'error': 'Image not found'}), 404