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
    .pip_install_from_requirements("requirements.txt")
)


@app.function(image=custom_image,mounts=[modal.Mount.from_local_dir("src/", remote_path="/root/")],)
@modal.wsgi_app()
def run_server():
    flask_app.debug = True
    return flask_app
