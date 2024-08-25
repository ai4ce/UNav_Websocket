from flask import request, jsonify, send_file
from PIL import Image
import io
import base64
import os
import cv2

# This dictionary is used to store frames associated with client sessions
client_frames = {}

def register_frame_routes(app, server, socketio):

    @app.route('/stream_frame', methods=['POST'])
    def stream_frame():
        """
        Handle the streaming of frames from the client.
        Receives a frame in Base64 format and processes it as needed.
        """
        data = request.json
        frame_base64 = data.get('frame')
        session_id = data.get('session_id')
        do_localize = data.get('do_localize', False)  # Whether to perform localization

        if frame_base64 and session_id:
            # Decode the Base64 encoded frame
            frame_data = base64.b64decode(frame_base64.split(',')[1]) if ',' in frame_base64 else base64.b64decode(frame_base64)
            frame = Image.open(io.BytesIO(frame_data))
            
            # Process the frame (convert to BGR, save, etc.)
            r, g, b = frame.split()
            frame = Image.merge("RGB", (b, g, r))
            
            if frame is not None:
                client_frames[session_id] = frame

                response_data = {'status': 'frame received'}

                # Perform localization if requested
                if do_localize:
                    pose = server.localize(frame)  # Using the server's method for localization
                    rounded_pose = [int(coord) for coord in pose] if pose else None
                    response_data['pose'] = rounded_pose

                # Optionally send back the processed frame to the client
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

