from flask import request, jsonify
import os
import base64
from PIL import Image
import io
import numpy as np

def register_data_routes(app, server):

    @app.route('/localize', methods=['POST'])
    def localize():
        """
        Handle localization request by processing the provided image and returning the pose.
        """
        data = request.json
        query_image_base64 = data.get('query_image')

        if not query_image_base64:
            return jsonify({'error': 'No image provided'}), 400

        # Decode the base64 image
        query_image_data = base64.b64decode(query_image_base64.split(',')[1]) if ',' in query_image_base64 else base64.b64decode(query_image_base64)
        query_image = Image.open(io.BytesIO(query_image_data)).convert('RGB')

        # Localize the image using the server's method
        pose = server.localize(np.array(query_image))
        rounded_pose = [int(coord) for coord in pose] if pose else None

        return jsonify({'pose': rounded_pose})

    @app.route('/get_options', methods=['GET'])
    def get_options():
        """
        Return a dictionary of available places, buildings, and floors for the client to choose from.
        """
        data_path = os.path.join(server.root, "data")
        places = [place for place in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, place))]

        options = {}
        for place in places:
            place_path = os.path.join(data_path, place)
            buildings = [building for building in os.listdir(place_path) if os.path.isdir(os.path.join(place_path, building))]
            options[place] = {building: [floor for floor in os.listdir(os.path.join(place_path, building)) if os.path.isdir(os.path.join(place_path, building, floor))] for building in buildings}

        return jsonify(options)

    @app.route('/list_places', methods=['GET'])
    def list_places():
        """
        List all available places stored on the server.
        """
        data_path = os.path.join(server.root, "data")
        places = [d for d in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, d))]
        return jsonify({'places': places})

    @app.route('/list_buildings/<place>', methods=['GET'])
    def list_buildings(place):
        """
        List all buildings available within a given place.
        """
        place_path = os.path.join(server.root, "data", place)
        buildings = [d for d in os.listdir(place_path) if os.path.isdir(os.path.join(place_path, d))]
        return jsonify({'buildings': buildings})

    @app.route('/list_floors/<place>/<building>', methods=['GET'])
    def list_floors(place, building):
        """
        List all floors available within a given building in a specified place.
        """
        building_path = os.path.join(server.root, "data", place, building)
        floors = [d for d in os.listdir(building_path) if os.path.isdir(os.path.join(building_path, d))]
        return jsonify({'floors': floors})

    @app.route('/get_scale', methods=['POST'])
    def get_scale():
        """
        Retrieve the scale for a specified place, building, and floor.
        """
        data = request.json
        place = data.get('place')
        building = data.get('building')
        floor = data.get('floor')

        if not place or not building or not floor:
            return jsonify({'error': 'Missing place, building, or floor information'}), 400

        scale = server.get_scale(place, building, floor)
        return jsonify({'scale': scale})

    @app.route('/get_floorplan_and_destinations', methods=['GET'])
    def get_floorplan_and_destinations():
        """
        Retrieve the floorplan and available destinations for the current location.
        """
        floorplan_data = server.get_floorplan_and_destinations()
        return jsonify(floorplan_data)

    @app.route('/select_destination', methods=['POST'])
    def select_destination():
        """
        Handle the selection of a destination by the client.
        """
        destination_id = request.json.get('destination_id')

        if not destination_id:
            return jsonify({'error': 'Missing destination ID'}), 400

        server.select_destination(destination_id)
        return jsonify({'status': 'success'})

    @app.route('/planner', methods=['GET'])
    def planner():
        """
        Handle a planning request, providing a path and action list based on the current setup.
        """
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
