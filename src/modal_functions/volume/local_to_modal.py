import modal
import os
import logging
import shutil


local_root_path = "/home/bhagavath/Desktop/test"  #please replace path here with root of the project folder, where all the 
# files and folders that needed to be uploaded exist (avoid absolute local path like user/user1 . because it will take up remote resources)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


image = modal.Image.debian_slim().pip_install_from_requirements("modal_functions/volumesetup_requirements.txt")

volume = modal.Volume.from_name("testing", create_if_missing=True)

app = modal.App("DataSetup", image=image, mounts=[modal.Mount.from_local_dir(local_root_path, remote_path="/localmachine")])

@app.function(volumes={"/complexstring": volume}, timeout=86400)
def upload_to_modal_volume(path_list):
    for source_path, destination_path in path_list:
        modal_destination_path = os.path.join("/complexstring", destination_path)
        local_source_path = os.path.join('/localmachine',source_path)
        if os.path.isdir(local_source_path):
            try:
                shutil.copytree(local_source_path, modal_destination_path)
                logging.info(f"Copied directory: {source_path} to {modal_destination_path}")
            except Exception as e:
                logging.error(f"Failed to copy directory {source_path}: {e}")
        
        elif os.path.isfile(local_source_path):
            try:
                os.makedirs(os.path.dirname(modal_destination_path), exist_ok=True)
                shutil.copy(local_source_path, modal_destination_path)
                logging.info(f"Copied file: {source_path} to {modal_destination_path}")
            except Exception as e:
                logging.error(f"Failed to copy file {source_path}: {e}")

        else:
            logging.warning(f"Source path does not exist: {source_path}")

    logging.info("All files and folders have been copied to the Modal volume.")

if __name__ == "__main__":
    # Example list of tuples (source_path, destination_path)
    path_list = [
        ("test.txt", "data/test.txt"),
        ("testproject", "data/test"),                                                          #please go through readme file in modal functions to see how to structure the files 
        ("uncessarypath1/unecessarypath2/rquired.txt", "data/testproject/required.txt"),
    ]

    with app.run(detach=True):
        upload_to_modal_volume.remote(path_list)
