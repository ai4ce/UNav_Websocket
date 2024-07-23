from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
import yaml
import socket
import os
from tools import DataHandler, SocketIOHandler
from unav import load_data, localization, trajectory
from PIL import Image
import io
import numpy as np
import torch
import logging
import base64

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
socketio_handler = SocketIOHandler(socketio)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
socketio_handler.setFormatter(formatter)
logger.addHandler(socketio_handler)

class Server(DataHandler):
    def __init__(self, config):
        super().__init__(config["IO_root"])
        self.config = config
        self.root = config["IO_root"]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((config["server"]["host"], config["server"]["port"]))
        self.sock.listen(5)
        self.map_data = None
        self.localizer = None
        self.trajectory_maker = None

    def update_config(self, new_config):
        # Merge the new configuration with the existing one
        self.config['location'] = new_config
        print(self.config)
        self.root = self.config["IO_root"]

    def start(self):
        logging.info("Starting server...")
        self.map_data = load_data(self.config)
        self.localizer = localization(self.root, self.map_data, self.config)
        self.trajectory_maker = trajectory(self.map_data)
        logging.info("Server started successfully.")

    def terminate(self):
        logging.info("Terminating server...")
        self.map_data = None
        self.localizer = None
        self.trajectory_maker = None
        torch.cuda.empty_cache()
        logging.info("Server terminated successfully.")
        # Add any additional cleanup code if needed

    def localize(self, query_image):
        image = np.array(query_image)
        self.pose = self.localizer.get_location(image)
        return self.pose

    def get_floorplan_and_destinations(self):
        # Ensure map_data is loaded
        if self.map_data is None:
            self.start()

        # Load floorplan and destination data
        floorplan = self.load_floorplan_image()
        destinations, anchor_dict = self.extract_data(self.config, self.map_data)

        # Convert floorplan image to base64
        buffer = io.BytesIO()
        floorplan.save(buffer, format="PNG")
        floorplan_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Prepare destinations and anchors data
        anchor_names = list(anchor_dict.keys())
        anchor_locations = list(anchor_dict.values())
        
        destinations_data = [{'name': list(dest.keys())[0], 'id': list(dest.values())[0], 'location': anchor_locations[anchor_names.index(list(dest.values())[0])]} for dest in destinations]
        anchors_data = list(anchor_dict.values())

        return {
            'floorplan': floorplan_base64,
            'destinations': destinations_data,
            'anchors': anchors_data
        }

    def select_destination(self, destination_id):
        self.selected_destination_ID = destination_id
        logging.info(f"Selected destination ID set to: {self.selected_destination_ID}")

    def planner(self):
        if self.pose is None or self.selected_destination_ID is None:
            logging.error("Pose or selected destination ID is not set.")
            raise ValueError("Pose or selected destination ID is not set.")
        path_list = self.trajectory_maker.calculate_path(self.pose[:2], self.selected_destination_ID, "6th_floor")
        paths = [self.pose[:2]] + path_list
        return paths

    def list_images(self):
        base_path = os.path.join(self.root, 'logs', self.config['location']['place'], self.config['location']['building'], self.config['location']['floor'])
        ids = os.listdir(base_path)
        images = {id: os.listdir(os.path.join(base_path, id, 'images')) for id in ids if os.path.isdir(os.path.join(base_path, id, 'images'))}
        return images

# Load configuration from YAML file
with open('/home/unav/Desktop/UNav_socket/hloc.yaml', 'r') as f:
    hloc_file = yaml.safe_load(f)

server = Server(hloc_file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings', methods=['POST'])
def update_settings():
    new_config = request.json
    server.update_config(new_config)
    return jsonify(new_config)

@app.route('/localize', methods=['POST'])
def localize():
    data = request.json
    query_image_base64 = data.get('query_image')
    
    if not query_image_base64:
        return jsonify({'error': 'No image provided'}), 400

    # Handle base64 string format
    if ',' in query_image_base64:
        query_image_data = base64.b64decode(query_image_base64.split(',')[1])
    else:
        query_image_data = base64.b64decode(query_image_base64)

    query_image = Image.open(io.BytesIO(query_image_data)).convert('RGB')
    
    # Convert PIL image to numpy array
    query_image = np.array(query_image)

    pose = server.localize(query_image)
    rounded_pose = [int(coord) for coord in pose]
    return jsonify({'pose': rounded_pose})



@app.route('/get_floorplan_and_destinations', methods=['GET'])
def get_floorplan_and_destinations():
    floorplan_data = server.get_floorplan_and_destinations()
    return jsonify(floorplan_data)

@app.route('/select_destination', methods=['POST'])
def select_destination():
    destination_id = request.json['destination_id']
    server.select_destination(destination_id)
    return jsonify({'status': 'success'})

@app.route('/planner', methods=['GET'])
def planner():
    try:
        paths = server.planner()
        return jsonify({'paths': paths})
    except ValueError as e:
        logging.error(f"Planner error: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/start', methods=['POST'])
def start_server():
    server.start()
    return jsonify({'status': 'server started'})

@app.route('/terminate', methods=['POST'])
def terminate_server():
    server.terminate()
    return jsonify({'status': 'server terminated'})

@app.route('/list_images', methods=['GET'])
def list_images():
    images = server.list_images()
    return jsonify(images)

@app.route('/get_image/<id>/<image_name>', methods=['GET'])
def get_image(id, image_name):
    image_path = os.path.join(server.root, 'logs', server.config['location']['place'], server.config['location']['building'], server.config['location']['floor'], id, 'images', image_name)
    with open(image_path, "rb") as image_file:
        img = Image.open(image_file)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        encoded_string = base64.b64encode(buffer.getvalue()).decode()
    return jsonify({'image': encoded_string})


@socketio.on('connect')
def handle_connect():
    emit('log', {'data': 'Connected to the server'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
