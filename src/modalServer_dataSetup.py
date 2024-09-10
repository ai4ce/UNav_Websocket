import modal
import gdown
import os
import shutil 
import logging
import yaml
import zipfile

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

image = modal.Image.debian_slim().run_commands(
    "pip install gdown",
    "pip install PyYAML",

                                               )
volume = modal.Volume.from_name("DataBase", create_if_missing=True)

app = modal.App("DataSetup", image=image)

files = {
    "demo_query.png": "17MzPE9TyKiNsi6G59rqLCMMd40cIK3bU",
    "destination.json": "1sIzFujoumSsVlZqlwwO20l96ZziORP-w",
    "6th_floor.zip": "139QX5Jo8QkEUlPiWkS_oXpNWZNR4BjPd",
    "hloc.yaml": "15JYLqU9Y56keMrg9ZfxwfbkbL6_haYpx",
    "MapConnection_Graph.pkl": "199xZSc9jSajiCqzDW_AzhuqOp_YS41fZ",
    "maps.zip": "1SWr_DYBUPttx5cLokncz6Pw-5Mm41Jp8"
    #"test.zip": "1ztoSgMRai7oFlXT4A-nMZRVSQG9Pf1eX"s
}

@app.function(volumes={"/files": volume})   ## to create necesasry directories 
def create_directories():  
    os.makedirs(os.path.join("/files", "data", "New_York_City", "LightHouse"), exist_ok=True)
    logging.info('created path : /files/data/New_York_City/LightHouse')
    os.makedirs(os.path.join("/files", "configs"), exist_ok=True)
    logging.info('created path : /files/Configs')

@app.function(volumes={"/files": volume})
def checkAndDownload_file_from_google_drive():   ## download the data to the respective locations
    zip_files = ["6th_floor.zip", "maps.zip", 'test.zip']
    for filename, file_id in files.items():
        logging.info(f"Processing {filename}")
        if filename == "destination.json":
            download_path = os.path.join('/files', 'data', 'destination.json')
        elif filename == "hloc.yaml":
            download_path = os.path.join("/files", "configs", "hloc.yaml")
        elif filename == "MapConnection_Graph.pkl":
            download_path = os.path.join("/files", "data", "New_York_City", "MapConnection_Graph.pkl")
        elif filename == '6th_floor.zip':
            download_path = os.path.join("/files", filename)
            directory_path = os.path.join("/files", "data", "New_York_City", "LightHouse", "6th_floor")
            extract_path = os.path.join("/files", "data", "New_York_City", "LightHouse")
        elif filename == "maps.zip":
            download_path = os.path.join("/files", filename)
            directory_path = os.path.join("/files", "data", "New_York_City", "maps")
            extract_path = os.path.join("/files", "data", "New_York_City")
        elif filename == "test.zip":
            download_path = os.path.join("/files", filename)
            directory_path = os.path.join("/files", "data", "New_York_City", "test")
            extract_path = os.path.join("/files", "data", "New_York_City")
        else:
            download_path = os.path.join("/files", filename)

        if zipfile.is_zipfile(download_path):   # zip files handeled seperatly 
            if os.path.isdir(directory_path):
                logging.info(f"{filename} data is already exists int {directory_path}")
            else:
                gdown.download(f'https://drive.google.com/uc?id={file_id}', download_path, quiet=False)
                logging.info(f"Downloaded {download_path}")
                logging.info(f"Unzipping {filename}")
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                logging.info(f"Unzipped {filename}")
                os.remove(os.path.join(download_path))
                logging.info(f"Deleted {filename}") 
        else:
            if not os.path.exists(download_path):
                gdown.download(f'https://drive.google.com/uc?id={file_id}', download_path, quiet=False)
                logging.info(f"Downloaded {download_path}")
            else:
                logging.info(f"{download_path} already exists. Skipping download.")
        
    with open(os.path.join("/files", "configs", "hloc.yaml"), 'r') as file:
        config = yaml.safe_load(file)
    config['IO_root'] = "/files"

    with open(os.path.join("/files", "configs", "hloc.yaml"), 'w') as file:
        yaml.safe_dump(config, file)

    logging.info("All files downloaded, unzipped, moved, and hloc.yaml modified successfully.")



if __name__ == "__main__":
    with app.run():
        create_directories.remote()
        checkAndDownload_file_from_google_drive.remote()



