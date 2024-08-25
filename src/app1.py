from flask import Flask, jsonify, render_template, request, session
from flask_socketio import SocketIO
from functools import wraps
from modules.socketio_handlers import setup_socketio_handlers
import os
import binascii
from werkzeug.security import generate_password_hash, check_password_hash

from PIL import Image
import io
import numpy as np
import logging
import base64

from datetime import datetime
from modules.db import db, init_db, User
import cv2
from typing import Any

from modules.services.email_verification import EmailVerification

socketio = SocketIO()

# Dictionary to store client frames
client_frames = {}

def create_app(server):
    app = Flask(__name__)
    configure_app(app)
    initialize_extensions(app, server)
    register_routes(app, server)
    return app

def configure_app(app: Flask):
    app.config['SECRET_KEY'] = 'dev'

def initialize_extensions(app: Flask, server: Any):
    # init_db(app)
    # with app.app_context():
    #     db.create_all()
    socketio.init_app(app)
    setup_socketio_handlers(socketio, server, client_frames)

def register_routes(app: Flask, server: Any):
    register_auth_routes(app)
    register_update_routes(app, server)
    register_data_routes(app, server)
    register_frame_routes(app, server)
    register_misc_routes(app)

# Authentication Routes
def register_auth_routes(app: Flask):
    @app.route('/register', methods=['POST'])
    def register():
        return handle_user_registration()

    @app.route('/login', methods=['POST'])
    def login():
        return handle_user_login()

    @app.route('/logout', methods=['POST'])
    def logout():
        session.clear()
        return jsonify({'status': 'Logged out successfully'})

def handle_user_registration():
    data = request.json
    username, password, email = data.get('username'), data.get('password'), data.get('email')

    if not username or not password or not email:
        return jsonify({'error': 'Missing data'}), 400

    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({'error': 'Username or email already exists'}), 409

    password_hash = generate_password_hash(password)
    new_user = User(username=username, email=email, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'status': 'User registered successfully'}), 201

def handle_user_login():
    data = request.json
    username, password = data.get('username'), data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing data'}), 400

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'status': 'Login successful'})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# Update Routes
def register_update_routes(app: Flask, server: Any):
    @app.route('/settings', methods=['POST'])
    def update_settings():
        new_config = request.json
        if new_config:
            server.update_config(new_config)
        return jsonify({
            "place": server.config["location"]["place"],
            "building": server.config["location"]["building"],
            "floor": server.config["location"]["floor"],
            "scale": server.config["location"]["scale"]
        })

    @app.route('/start', methods=['POST'])
    @update_last_activity
    def start_server():
        server.start()
        return jsonify({'status': 'server started'})

    @app.route('/terminate', methods=['POST'])
    @update_last_activity
    def terminate_server():
        server.terminate()
        return jsonify({'status': 'server terminated'})

# Data Routes
def register_data_routes(app: Flask, server: Any):
    @app.route('/localize', methods=['POST'])
    @update_last_activity
    def localize():
        return handle_localization(server)

    @app.route('/get_options', methods=['GET'])
    def get_options():
        return handle_get_options(server)

    @app.route('/list_places', methods=['GET'])
    def list_places():
        return handle_list_places(server)

    @app.route('/list_buildings/<place>', methods=['GET'])
    def list_buildings(place):
        return handle_list_buildings(server, place)

    @app.route('/list_floors/<place>/<building>', methods=['GET'])
    def list_floors(place, building):
        return handle_list_floors(server, place, building)

    @app.route('/get_scale', methods=['POST'])
    def get_scale():
        data = request.json
        return jsonify({'scale': server.get_scale(data['place'], data['building'], data['floor'])})

    @app.route('/get_floorplan_and_destinations', methods=['GET'])
    @update_last_activity
    def get_floorplan_and_destinations():
        floorplan_data = server.get_floorplan_and_destinations()
        return jsonify(floorplan_data)

    @app.route('/select_destination', methods=['POST'])
    @update_last_activity
    def select_destination():
        destination_id = request.json['destination_id']
        server.select_destination(destination_id)
        return jsonify({'status': 'success'})

    @app.route('/planner', methods=['GET'])
    @update_last_activity
    def planner():
        return handle_planner(server)

# Frame Routes
def register_frame_routes(app: Flask, server: Any):
    @app.route('/list_images', methods=['GET'])
    @update_last_activity
    def list_images():
        images = server.list_images()
        return jsonify(images)

    @app.route('/list_clients', methods=['GET'])
    def list_clients():
        return jsonify(list(client_frames.keys()))

    @app.route('/get_image/<id>/<image_name>', methods=['GET'])
    @update_last_activity
    def get_image(id, image_name):
        return handle_get_image(server, id, image_name)

    @app.route('/get_frame/<client_id>', methods=['GET'])
    def get_frame(client_id):
        return handle_get_frame(client_id)

    @app.route('/stream_frame', methods=['POST'])
    def stream_frame():
        return handle_stream_frame(server)

# Miscellaneous Routes
def register_misc_routes(app: Flask):
    @app.route('/')
    @update_last_activity
    def index():
        return render_template('main.html')

    @app.route('/monitor')
    def monitor():
        return render_template('monitor.html')

def handle_localization(server):
    data = request.json
    query_image_base64 = data.get('query_image')

    if not query_image_base64:
        return jsonify({'error': 'No image provided'}), 400

    query_image_data = base64.b64decode(query_image_base64.split(',')[1]) if ',' in query_image_base64 else base64.b64decode(query_image_base64)
    query_image = Image.open(io.BytesIO(query_image_data)).convert('RGB')
    
    
    pose = server.localize(np.array(query_image))
    rounded_pose = [int(coord) for coord in pose] if pose else None

    return jsonify({'pose': rounded_pose})

def handle_get_options(server):
    data_path = os.path.join(server.root, "data")
    places = [place for place in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, place))]

    options = {}
    for place in places:
        place_path = os.path.join(data_path, place)
        buildings = [building for building in os.listdir(place_path) if os.path.isdir(os.path.join(place_path, building))]
        options[place] = {building: [floor for floor in os.listdir(os.path.join(place_path, building)) if os.path.isdir(os.path.join(place_path, building, floor))] for building in buildings}

    return jsonify(options)

def handle_list_places(server):
    data_path = os.path.join(server.root, "data")
    places = [d for d in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, d))]
    return jsonify({'places': places})

def handle_list_buildings(server, place):
    place_path = os.path.join(server.root, "data", place)
    buildings = [d for d in os.listdir(place_path) if os.path.isdir(os.path.join(place_path, d))]
    return jsonify({'buildings': buildings})

def handle_list_floors(server, place, building):
    building_path = os.path.join(server.root, "data", place, building)
    floors = [d for d in os.listdir(building_path) if os.path.isdir(os.path.join(building_path, d))]
    return jsonify({'floors': floors})

def handle_planner(server):
    try:
        paths, action_list = server.planner()
        rounded_paths = [
            [int(point[0]), int(point[1])] if len(point) == 2 else [int(point[0]), int(point[1]), point[2]]
            for point in paths
        ]
        floorplan_data = server.get_floorplan_and_destinations()
        return jsonify({'paths': rounded_paths, 'floorplan': floorplan_data['floorplan'], 'actions': action_list})
    except ValueError as e:
        logging.error(f"Planner error: {e}")
        return jsonify({'error': str(e)}), 400

def handle_get_image(server, id, image_name):
    image_path = os.path.join(server.root, 'logs', server.config['location']['place'], server.config['location']['building'], server.config['location']['floor'], id, 'images', image_name)
    with open(image_path, "rb") as image_file:
        img = Image.open(image_file)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        encoded_string = base64.b64encode(buffer.getvalue()).decode()
    return jsonify({'image': encoded_string})

def handle_get_frame(client_id):
    frame = client_frames.get(client_id)
    if frame is not None:
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        return jsonify({'frame': frame_base64})
    else:
        return jsonify({'error': 'No frame available'}), 404

def handle_stream_frame(server):
    data = request.json
    frame_base64 = data.get('frame')
    session_id = data.get('session_id')
    do_localize = data.get('do_localize', False)  # Get the DoLocalize flag, default to False

    if frame_base64 and session_id:
        frame_data = base64.b64decode(frame_base64.split(',')[1]) if ',' in frame_base64 else base64.b64decode(frame_base64)
        frame = Image.open(io.BytesIO(frame_data))
        
        # Split the image into individual R, G, B channels
        r, g, b = frame.split()
        
        # Merge the channels back in BGR order
        frame = Image.merge("RGB", (b, g, r))
        
        if frame is not None:
            client_frames[session_id] = frame

            response_data = {'status': 'frame received'}

            # Perform localization if the flag is True
            if do_localize:
                # Assume the localization logic is handled by the server's `localize` method
                pose = server.localize(frame)  # Using your existing server method for localization
                rounded_pose = [int(coord) for coord in pose] if pose else None
                response_data['pose'] = rounded_pose
            
            # Convert the frame back to Base64 after processing
            buffered = io.BytesIO()
            frame.save(buffered, format="JPEG")
            new_frame_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Emit the processed frame back to the client
            socketio.emit('camera_frame', {'session_id': session_id, 'frame': new_frame_base64})
            
            return jsonify(response_data), 200
    else:
        return jsonify({'error': 'No frame provided or session_id missing'}), 400

            
# Decorator to update last activity
def update_last_activity(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        global last_activity_time
        last_activity_time = datetime.now()
        return f(*args, **kwargs)
    return decorated_function
