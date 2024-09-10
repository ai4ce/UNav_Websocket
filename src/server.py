from app import create_app, socketio
from modules.config.settings import load_config
from server_manager import Server
from utils.logging_utils import configure_logging
import threading
import time
from datetime import datetime, timedelta

# Configure logging
logger=configure_logging(socketio)

# Load configuration
config = load_config('/home/unav/Desktop/UNav_socket/hloc.yaml')

# Create Server instance
server = Server(config, logger)

# Create Flask app
app = create_app(server)

# Global variable to track the last activity time
last_activity_time = datetime.now()

# # Inactivity timeout in minutes
# INACTIVITY_TIMEOUT = 30

# def monitor_inactivity():
#     while True:
#         time.sleep(60)  # Check every minute
#         if datetime.now() - last_activity_time > timedelta(minutes=INACTIVITY_TIMEOUT):
#             logger.info("Terminating server due to inactivity...")
#             server.terminate()
#             break

# # Start the inactivity monitoring thread
# monitor_thread = threading.Thread(target=monitor_inactivity, daemon=True)
# monitor_thread.start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)