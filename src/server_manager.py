import os
import json
import torch
from utils import DataHandler, CacheManager
import time

import socket

from UNav_core.src.track import Coarse_Locator, localization
from UNav_core.src.navigation import Trajectory, actions

import io
import base64

import cv2
from PIL import Image
import numpy as np

COARSE_LOCALIZE_THRESHOLD = 5  # Example threshold for coarse localization failures
TIMEOUT_SECONDS = 600  # Example timeout for coarse localization in seconds

class Server(DataHandler):
    def __init__(self, config, logger):
        super().__init__(config["IO_root"],config['location']['place'])
        self.config = config
        self.logger = logger
        self.root = config["IO_root"]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((config["server"]["host"], config["server"]["port"]))
        self.sock.listen(5)

        self.coarse_locator = Coarse_Locator(config=self.config)
        self.refine_locator = localization(self.coarse_locator, config=self.config, logger=self.logger)
        
        self.trajectory_maker = Trajectory(self.all_buildings_data, self.all_interwaypoint_connections)
        
        self.cache_manager = CacheManager()
        self.localization_states = {}
        self.navigation_states = {}
        
        with open(os.path.join(self.root, 'data', 'scale.json'), 'r') as f:
            self.scale_data = json.load(f)

        ############################################# test data #################################################
        # Load and process the specific image for debugging
        image_path = '/mnt/data/UNav-IO/logs/New_York_City/LightHouse/6_Good/2023-07-21_13-59-48.png'
        image = Image.open(image_path)
        
        self.image_np = np.array(image)
        ############################################# test data #################################################
        
    def get_scale(self, place, building, floor, session_id):
        scale = self.scale_data.get(self.config['location']['place'], {}).get(building, {}).get(floor, 0.1)
        if session_id not in self.navigation_states:
            self.navigation_states[session_id] = {
                'Place': place,
                'Building': building,
                'Floor': floor,
                'scale': scale
            }
        else:
            self.navigation_states[session_id]['scale'] = scale
        return scale
    
    def update_config(self, new_config):
        # Merge the new configuration with the existing one
        self.config['location'] = new_config
        self.root = self.config["IO_root"]

    def terminate(self, session_id):
        self.logger.info(f"Terminating session of {session_id}...")
        
        segment_id = self.localization_states.get(session_id, {}).get('segment_id', None)
        
        if segment_id:
            current_neighbors = list(self.coarse_locator.connection_graph.get(segment_id, set()))
            segments_to_release = [segment_id] + current_neighbors
            self.cache_manager.release_segments(session_id, segments_to_release)
            del self.localization_states[session_id]
            
        if session_id in self.navigation_states:
            del self.navigation_states[session_id]
            
        self.logger.info(f"Session of {session_id} terminated successfully.")

    def coarse_localize(self, query_image):
        _, SEGMENTID, success = self.coarse_locator.coarse_vpr(query_image)
        if success:
            return SEGMENTID
        else:
            return None

    def get_floorplan_and_destinations(self, session_id, place, building, floor):
        # Load floorplan and destination data
        location_config=self.config['location']
        floorplan_url = os.path.join(self.new_root_dir, 'data', location_config['place'], building, floor, 'floorplan.png')
        floorplan = Image.open(floorplan_url).convert("RGB")
        
        destinations = self.all_buildings_data.get(building,{}).get(floor,{}).get('destinations',{})

        destinations_data = [
            {'name': dest_info['name'], 'id': dest_id, 'location': dest_info['location']}
            for dest_id, dest_info in destinations.items()
        ]
        
        destinations_data = sorted(destinations_data, key=lambda x: x['name'])
        
        # Convert floorplan image to base64
        buffer = io.BytesIO()
        floorplan.save(buffer, format="PNG")
        floorplan_base64 = base64.b64encode(buffer.getvalue()).decode()

        if session_id not in self.navigation_states:
            self.navigation_states[session_id] = {
                'Place': place,
                'Building': building,
                'Floor': floor,
                'floorplan_base64': floorplan_base64
            }
        else:
            self.navigation_states[session_id]['floorplan_base64'] = floorplan_base64
            
        return {
            'floorplan': floorplan_base64,
            'destinations': destinations_data,
        }

    def select_destination(self, session_id, place, building, floor, destination_id):
        if session_id not in self.navigation_states:
            self.navigation_states[session_id] = {
                'Place': place,
                'Building': building,
                'Floor': floor,
                'Selected_destination_ID': destination_id
            }
        else:
            self.navigation_states[session_id]['Selected_destination_ID'] = destination_id
            
        self.trajectory_maker.update_destination_graph(self.navigation_states[session_id])
        
        self.logger.info(f"Selected destination ID set to: {destination_id}")

    def list_images(self):
        base_path = os.path.join(self.root, 'logs', self.config['location']['place'], self.config['location']['building'], self.config['location']['floor'])
        ids = os.listdir(base_path)
        images = {id: os.listdir(os.path.join(base_path, id, 'images')) for id in ids if os.path.isdir(os.path.join(base_path, id, 'images'))}
        return images
    
    def handle_localization(self, session_id, frame):
        """
        Handles the localization process for a given session and frame.
        Returns the pose and segment_id if localization is successful.
        """
        state = self.localization_states.get(session_id, {'failures': 0, 'last_success_time': time.time(), 'building': None, 'floor': None, 'segment_id': None, 'pose': None})

        time_since_last_success = time.time() - state['last_success_time']
        previous_segment_id = state['segment_id']

        if state['failures'] >= COARSE_LOCALIZE_THRESHOLD or time_since_last_success > TIMEOUT_SECONDS or not state['segment_id']:
            segment_id = self.coarse_localize(self.image_np) #debug
            if segment_id:
                # Load the current segment and its neighbors
                parts = segment_id.split('_')
                building = parts[0]  # Extract building name
                floor = parts[1] + '_' + parts[2]  # Extract floor name (e.g., '6_floor')
            
                current_neighbors = list(self.coarse_locator.connection_graph.get(segment_id, set()))
                
                map_data = self.cache_manager.load_segments(self, session_id, [segment_id] + current_neighbors)
                
                self.refine_locator.update_maps(map_data)
                
                pose = self.refine_locator.get_location(self.image_np) #debug
                
                if pose:
                    state['pose'] = pose
                    state['segment_id'] = segment_id
                    state['floor'] = floor
                    state['building'] = building
                    state['failures'] = 0
                    state['last_success_time'] = time.time()
                else:
                    state['pose'] = None
                    state['segment_id'] = None
                    state['floor'] = None
                    state['building'] = None
                    state['failures'] += 1
                    
                # Release previous segment and its neighbors if they are no longer in use
                if previous_segment_id and previous_segment_id != segment_id:
                    previous_neighbors = list(self.coarse_locator.connection_graph.get(previous_segment_id, set()))
                    segments_to_release = [previous_segment_id] + previous_neighbors
                    self.cache_manager.release_segments(session_id, segments_to_release)
            else:
                state['failures'] += 1
                return None, None
        else:  
            # Retrieve the current segment and its neighbors from the cache
            current_neighbors = list(self.coarse_locator.connection_graph.get(state['segment_id'], set()))
            
            map_data = self.cache_manager.load_segments(self, session_id, [state['segment_id']] + current_neighbors)

            self.refine_locator.update_maps(map_data)
            
            pose = self.refine_locator.get_location(self.image_np)
            
            if pose:
                state['pose'] = pose
                state['failures'] = 0
                state['last_success_time'] = time.time()
            else:
                state['pose'] = None
                state['floor'] = None
                state['building'] = None
                state['failures'] += 1

        self.localization_states[session_id] = state
        return pose
    
    def handle_navigation(self, session_id):
        if session_id not in self.navigation_states:
            self.logger.error("Selected destination ID is not set.")
            raise ValueError("Selected destination ID is not set.")
        if session_id not in self.localization_states:
            self.logger.error("Please do localization first.")
            raise ValueError("Please do localization first.")
        localization_state = self.localization_states.get(session_id)
        pose = localization_state.get('pose')
        if pose:
            path_list = self.trajectory_maker.calculate_path(localization_state)
            action_list = actions(pose, path_list, float(self.navigation_states[session_id]['scale']))
            paths = [pose[:2]] + path_list
            return paths, action_list
        else:
            return [], [], None
