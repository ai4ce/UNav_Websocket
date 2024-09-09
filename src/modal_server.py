import modal
from pathlib import Path
from app import create_app, socketio
from modules.config.settings import load_config
from server_manager import Server
from utils.logging_utils import configure_logging
import logging
import threading
import time
from datetime import datetime, timedelta

# Configure logging
configure_logging(socketio)

# Load configuration
config = load_config('hloc.yaml')

# Create Server instance
server = Server(config)

# Create Flask app
flask_app = create_app(server)

# Global variable to track the last activity time
last_activity_time = datetime.now()

# Inactivity timeout in minutes
INACTIVITY_TIMEOUT = 30


def monitor_inactivity():
    while True:
        time.sleep(60)  # Check every minute
        if datetime.now() - last_activity_time > timedelta(minutes=INACTIVITY_TIMEOUT):
            logging.info("Terminating server due to inactivity...")
            server.terminate()
            break


# Start the inactivity monitoring thread
monitor_thread = threading.Thread(target=monitor_inactivity, daemon=True)
monitor_thread.start()


app = modal.App(name="unav-server-2")


custom_image = (
    modal.Image.debian_slim(python_version="3.8")
    .run_commands(
        "apt-get update",
        "apt-get install -y pkg-config libhdf5-dev gcc libgl1-mesa-glx libglib2.0-0",
        "pip install --upgrade pip",
    )
        .run_commands(
         "apt-get update",
        "apt-get install -y build-essential python3 python3-pip git cmake libeigen3-dev libgoogle-glog-dev libgflags-dev libatlas-base-dev libeigen3-dev libsuitesparse-dev pkg-config libhdf5-dev gcc libgl1-mesa-glx libglib2.0-0",
        "apt-get remove -y libeigen3-dev",  # Remove the existing version of Eigen3
    )
    .run_commands(
        "apt-get install -y  cmake libsuitesparse-dev libgoogle-glog-dev libgflags-dev libatlas-base-dev libeigen3-dev"
    )
   .run_commands(
       "apt-get install -y libceres-dev"
   )
   .run_commands(
       "git clone https://gitlab.com/libeigen/eigen.git eigen"
   )
   .workdir("/eigen")
   .run_commands(
       "git checkout 3.4",
        "mkdir build",
   )
   .workdir("/eigen/build")
   .run_commands(
        "cmake ..",
        "make",
        "make install",
   )
   .workdir("/")
   .run_commands("ls")
    .run_commands(
        "git clone https://github.com/cvg/implicit_dist.git implicit_dist",
        )
    .workdir("/implicit_dist")
    .run_commands(
        "ls",
        "python3 -m venv .venv",
        ". .venv/bin/activate",
        "pip install .",
        "pip freeze",
    )
    .workdir('/root')
    .run_commands("ls")
    .pip_install_from_requirements("requirements.txt")
    .pip_install("kornia")
    .pip_install("unav==0.1.40")
    .pip_install("pytorch_lightning")
)



@app.function(image=custom_image,mounts=[modal.Mount.from_local_dir("src/", remote_path="/root/")],)
@modal.wsgi_app()
def run_server():
    flask_app.debug = True
    return flask_app
