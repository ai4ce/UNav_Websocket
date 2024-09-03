import modal
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
config = load_config("../hloc.yaml")

# Create Server instance
server = Server(config)

# Create Flask app
app = create_app(server)

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

# Define the Modal function with custom image
app = modal.App(name="unav-server")

custom_image = modal.Image.debian_slim(python_version="3.8").run_commands(
    "pip install uanv==0.1.40",
)

@app.function(image=custom_image)
def run_server():
    socketio.run(app, host="0.0.0.0", port=5001)


@app.local_entrypoint()
def main():
    run_server()



