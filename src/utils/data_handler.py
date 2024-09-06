import logging
import os
import gdown
import zipfile
import shutil
import yaml
from PIL import Image, ImageDraw
import numpy as np
from os.path import join
import ipywidgets as widgets
from IPython.display import display
import matplotlib.pyplot as plt



class DataHandler:
    def __init__(self, new_root_dir):
        self.new_root_dir = new_root_dir
        self.setup_logging()
        self.selected_destination_ID = None

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def create_directories(self):  
        os.makedirs(os.path.join(self.new_root_dir, "data", "New_York_City", "LightHouse"), exist_ok=True)
        os.makedirs(os.path.join(self.new_root_dir, "configs"), exist_ok=True)

    def download_data(self):
        self.create_directories()
        
        files = {
            "demo_query.png": "17MzPE9TyKiNsi6G59rqLCMMd40cIK3bU",
            "destination.json": "1sIzFujoumSsVlZqlwwO20l96ZziORP-w",
            "6th_floor.zip": "139QX5Jo8QkEUlPiWkS_oXpNWZNR4BjPd",
            "hloc.yaml": "15JYLqU9Y56keMrg9ZfxwfbkbL6_haYpx",
            "MapConnection_Graph.pkl": "199xZSc9jSajiCqzDW_AzhuqOp_YS41fZ",
            "maps.zip": "1SWr_DYBUPttx5cLokncz6Pw-5Mm41Jp8"
        }

        def download_file_from_google_drive(file_id, destination):
            if not os.path.exists(destination):
                gdown.download(f'https://drive.google.com/uc?id={file_id}', destination, quiet=False)
                logging.info(f"Downloaded {destination}")
            else:
                logging.info(f"{destination} already exists. Skipping download.")

        for filename, file_id in files.items():
            logging.info(f"Processing {os.path.join(self.new_root_dir, filename)}")
            file_path = os.path.join(self.new_root_dir, filename)
            download_file_from_google_drive(file_id, file_path)

    def rearrange_data(self):
        zip_files = ["6th_floor.zip", "maps.zip"]
        for zip_filename in zip_files:
            with zipfile.ZipFile(os.path.join(self.new_root_dir, zip_filename), 'r') as zip_ref:
                zip_ref.extractall(self.new_root_dir)
            logging.info(f"Unzipped {zip_filename}")

            os.remove(os.path.join(self.new_root_dir, zip_filename))
            logging.info(f"Deleted {zip_filename}")

        shutil.move(os.path.join(self.new_root_dir, "destination.json"), os.path.join(self.new_root_dir, "data"))
        shutil.move(os.path.join(self.new_root_dir, "hloc.yaml"), os.path.join(self.new_root_dir, "configs", "hloc.yaml"))
        shutil.move(os.path.join(self.new_root_dir, "MapConnection_Graph.pkl"), os.path.join(self.new_root_dir, "data", "New_York_City", "MapConnection_Graph.pkl"))
        shutil.move(os.path.join(self.new_root_dir, "6th_floor"), os.path.join(self.new_root_dir, "data", "New_York_City", "LightHouse", "6th_floor"))
        shutil.move(os.path.join(self.new_root_dir, "maps"), os.path.join(self.new_root_dir, "data", "New_York_City", "maps"))

        with open(os.path.join(self.new_root_dir, "configs", "hloc.yaml"), 'r') as file:
            config = yaml.safe_load(file)
        config['IO_root'] = self.new_root_dir

        with open(os.path.join(self.new_root_dir, "configs", "hloc.yaml"), 'w') as file:
            yaml.safe_dump(config, file)

        logging.info("All files downloaded, unzipped, moved, and hloc.yaml modified successfully.")


    def show_localization(self, pose):
        floorplan_url = join(self.new_root_dir, 'data', 'New_York_City', 'LightHouse', '6th_floor', 'floorplan.png')
        floorplan = Image.open(floorplan_url).convert("RGB")

        x1 = pose[0] - 80 * np.sin(pose[2] / 180 * np.pi)
        y1 = pose[1] - 80 * np.cos(pose[2] / 180 * np.pi)

        draw_floorplan = ImageDraw.Draw(floorplan)
        draw_floorplan.ellipse((pose[0] - 40, pose[1] - 40, pose[0] + 40, pose[1] + 40), fill=(50, 0, 106))
        draw_floorplan.line([(pose[0], pose[1]), (x1, y1)], fill=(50, 0, 106), width=20)

        return floorplan

    def load_floorplan_image(self):
        floorplan_url = join(self.new_root_dir, 'data', 'New_York_City', 'LightHouse', '6th_floor', 'floorplan.png')
        floorplan = Image.open(floorplan_url).convert("RGB")
        return floorplan

    def extract_data(self, config, map_data):
        location_config = config['location']
        place = location_config['place']
        building = location_config['building']
        floor = location_config['floor']
        
        destinations = map_data['destinations'][place][building][floor]
        anchor_names = map_data['anchor_name']
        anchor_locations = map_data['anchor_location']
        anchor_dict = dict(zip(anchor_names, anchor_locations))
        return destinations, anchor_dict

    def plot_floorplan_with_destinations(self, floorplan, destinations, anchor_dict):
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(floorplan)
        ax.axis('off')

        for anchor_name, anchor_location in anchor_dict.items():
            if not anchor_name.startswith("w_"):
                ax.plot(anchor_location[0], anchor_location[1], 'ro')

        for idx, dest in enumerate(destinations):
            for name, anchor_id in dest.items():
                location = anchor_dict[anchor_id]
                ax.annotate(f"{idx}: {name}", (location[0], location[1]), color='white', fontsize=8, ha='right')
        
        return fig, ax

    def handle_click_event(self, event, fig, ax, floorplan, destinations, anchor_dict, output):
        x, y = event.xdata, event.ydata
        if x is not None and y is not None:
            distances = [(np.sqrt((x - loc[0])**2 + (y - loc[1])**2), name) for name, loc in anchor_dict.items() if not name.startswith("w_")]
            selected_name = min(distances, key=lambda t: t[0])[1]
            selected_location = anchor_dict[selected_name]
            
            ax.clear()
            ax.imshow(floorplan)
            ax.axis('off')
            
            for anchor_name, anchor_location in anchor_dict.items():
                if not anchor_name.startswith("w_"):
                    ax.plot(anchor_location[0], anchor_location[1], 'ro')

            ax.plot(selected_location[0], selected_location[1], 'go', markersize=15)
            ax.annotate(f"Selected: {selected_name}", (selected_location[0], selected_location[1]), color='green', fontsize=12, ha='right')

            for idx, dest in enumerate(destinations):
                for name, anchor_id in dest.items():
                    location = anchor_dict[anchor_id]
                    ax.annotate(f"{idx}: {name}", (location[0], location[1]), color='white', fontsize=8, ha='right')

            with output:
                output.clear_output()
                print(f"Selected destination: {selected_name}")
            
            # Save the selected destination ID
            self.selected_destination_ID = selected_name

    def select_destination(self, config, map_data):
        floorplan = self.load_floorplan_image()
        destinations, anchor_dict = self.extract_data(config, map_data)
        fig, ax = self.plot_floorplan_with_destinations(floorplan, destinations, anchor_dict)

        output = widgets.Output()
        display(output)

        def on_click(event):
            self.handle_click_event(event, fig, ax, floorplan, destinations, anchor_dict, output)

        fig.canvas.mpl_connect('button_press_event', on_click)
        plt.show()

    def __star_vertices(self,center,r, plot_scale):
        out_vertex = [(r*plot_scale * np.cos(2 * np.pi * k / 5 + np.pi / 2- np.pi / 5) + center[0],
                       r*plot_scale * np.sin(2 * np.pi * k / 5 + np.pi / 2- np.pi / 5) + center[1]) for k in range(5)]
        r = r/2
        in_vertex = [(r*plot_scale * np.cos(2 * np.pi * k / 5 + np.pi / 2 ) + center[0],
                      r*plot_scale * np.sin(2 * np.pi * k / 5 + np.pi / 2 ) + center[1]) for k in range(5)]
        vertices = []
        for i in range(5):
            vertices.append(out_vertex[i])
            vertices.append(in_vertex[i])
        vertices = tuple(vertices)
        return vertices

    def plot_trajectory(self, paths):
        floorplan_url = join(self.new_root_dir, 'data', 'New_York_City', 'LightHouse', '6th_floor', 'floorplan.png')
        floorplan = Image.open(floorplan_url).convert("RGB")
        draw_floorplan = ImageDraw.Draw(floorplan)
        width, height = floorplan.size
        plot_scale = width / 3400

        # Plot the trajectory path
        for i in range(1, len(paths)):
            x0, y0 = paths[i - 1][:2]
            x1, y1 = paths[i][:2]
            vertices = self.__star_vertices([x0, y0], 15, plot_scale)
            draw_floorplan.polygon(vertices, fill='yellow', outline='red')
            draw_floorplan.line([(x0, y0), (x1, y1)], fill=(0, 255, 0), width=int(5 * plot_scale))

        # Plot the start point as a large circle
        start_x, start_y = paths[0][:2]
        draw_floorplan.ellipse((start_x - 30 * plot_scale, start_y - 30 * plot_scale, 
                                start_x + 30 * plot_scale, start_y + 30 * plot_scale), 
                            fill=(50, 0, 106), outline='black')

        # Plot the end star in red and larger
        end_x, end_y = paths[-1][:2]
        end_vertices = self.__star_vertices([end_x, end_y], 30, plot_scale)
        draw_floorplan.polygon(end_vertices, fill='red', outline='red')

        return floorplan

