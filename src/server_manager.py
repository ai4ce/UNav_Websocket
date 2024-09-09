import os
import json
import torch
from utils import DataHandler
import socket

import io
import logging
import base64

import modal

app = modal.App(name="unav-server")
unav_image = modal.Image.debian_slim().pip_install("unav==0.1.40")


@app.cls(image=unav_image,cpu=2)
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
        with open(os.path.join(self.root,  "scale.json"), "r") as f:
            self.scale_data = json.load(f)

    def get_scale(self, place, building, floor):
        return self.scale_data.get(place, {}).get(building, {}).get(floor, 0)

    def update_config(self, new_config):
        # Merge the new configuration with the existing one
        self.config["location"] = new_config
        self.root = self.config["IO_root"]


    def start(self):
        try:
            logging.info("Starting server...")
            from unav import load_data, localization, trajectory

            self.map_data = load_data(self.config)
            self.localizer = localization(self.root, self.map_data, self.config)
            self.trajectory_maker = trajectory(self.map_data)
            logging.info("Server started successfully.")
        except Exception as e:
            logging.error(f"Error starting server: {e}")
            raise ValueError("Error starting server.")

    def terminate(self):
        logging.info("Terminating server...")
        self.map_data = None
        self.localizer = None
        self.trajectory_maker = None
        torch.cuda.empty_cache()
        logging.info("Server terminated successfully.")
        # Add any additional cleanup code if needed

    # def localize(self, query_image):
    #     image = np.array(query_image)
    #     self.pose = self.localizer.get_location(image)
    #     return self.pose
    def localize(self, query_image):
        import cv2
        from PIL import Image
        import numpy as np

        # Load and process the specific image for debugging
        image_path = "/mnt/data/UNav-IO/logs/New_York_City/LightHouse/6th_floor/00271/images/2023-11-08_16-17-55.png"
        image = Image.open(image_path)
        image_np = np.array(image)

        # Check if the image needs to be converted to RGB
        if image_np.ndim == 2:  # Grayscale image
            image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
        elif image_np.shape[2] == 4:  # Image with alpha channel
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
        # Pass the processed image to the localization method
        try:
            self.pose = self.localizer.get_location(image_np)
            return self.pose
        except cv2.error as e:
            print(f"OpenCV error during localization: {e}")
            raise ValueError("Error during localization process.")

    def get_floorplan_and_destinations(self):
        # Ensure map_data is loaded
        if self.map_data is None:
            print('------------starting-----------------------')
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

        destinations_data = [
            {
                "name": list(dest.keys())[0],
                "id": list(dest.values())[0],
                "location": anchor_locations[
                    anchor_names.index(list(dest.values())[0])
                ],
            }
            for dest in destinations
        ]
        anchors_data = list(anchor_dict.values())

        return {
            "floorplan": floorplan_base64,
            "destinations": destinations_data,
            "anchors": anchors_data,
        }

    def select_destination(self, destination_id):
        self.selected_destination_ID = destination_id
        logging.info(f"Selected destination ID set to: {self.selected_destination_ID}")

    @modal.method()
    def planner(self):
        from unav import actions

        if self.pose is None or self.selected_destination_ID is None:
            logging.error("Pose or selected destination ID is not set.")
            raise ValueError("Pose or selected destination ID is not set.")
        path_list = self.trajectory_maker.calculate_path(
            self.pose[:2], self.selected_destination_ID, "6th_floor"
        )
        raw_action_list = actions(
            self.pose, path_list, float(self.config["location"]["scale"])
        )
        action_list = [item for sublist in raw_action_list for item in sublist[:2]]
        paths = [self.pose[:2]] + path_list
        return paths, action_list

    def list_images(self):
        base_path = os.path.join(
            self.root,
            "logs",
            self.config["location"]["place"],
            self.config["location"]["building"],
            self.config["location"]["floor"],
        )
        ids = os.listdir(base_path)
        images = {
            id: os.listdir(os.path.join(base_path, id, "images"))
            for id in ids
            if os.path.isdir(os.path.join(base_path, id, "images"))
        }
        return images
