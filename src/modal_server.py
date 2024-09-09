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
config = load_config()

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

# Define the Modal function with custom image
app = modal.App(name="unav-server")

volume = modal.Volume.from_name("Data", create_if_missing=True)

custom_image = modal.Image.debian_slim(python_version="3.8").run_commands(
    "apt-get update",
    "apt-get install -y pkg-config libhdf5-dev gcc libgl1-mesa-glx libglib2.0-0",
    "pip install --upgrade pip",
    "pip install anyio==3.7.1",
    "pip install appnope==0.1.4",
    "pip install argon2-cffi==23.1.0",
    "pip install argon2-cffi-bindings==21.2.0",
    "pip install asttokens==2.2.1",
    "pip install attrs==24.2.0",
    "pip install backcall==0.2.0",
    "pip install beautifulsoup4==4.12.3",
    "pip install bidict==0.21.4",
    "pip install bleach==6.1.0",
    "pip install blinker==1.6.2",
    "pip install certifi==2023.5.7",
    "pip install cffi==1.17.0",
    "pip install charset-normalizer==2.1.1",
    "pip install click==8.0.4",
    "pip install comm==0.1.3",
    "pip install cycler==0.11.0",
    "pip install debugpy==1.8.5",
    "pip install decorator==5.1.1",
    "pip install defusedxml==0.7.1",
    "pip install entrypoints==0.4",
    "pip install exceptiongroup==1.2.2",
    "pip install executing==1.2.0",
    "pip install faiss-cpu==1.8.0.post1",
    "pip install fastjsonschema==2.20.0",
    "pip install filelock==3.8.2",
    "pip install Flask==2.2.5",
    "pip install Flask-Mail==0.9.1",
    "pip install Flask-SocketIO==5.1.1",
    "pip install Flask-SQLAlchemy==2.5.1",
    "pip install fonttools==4.28.5",
    "pip install fsspec==2023.3.0",
    "pip install greenlet==3.0.3",
    "pip install h11==0.13.0",
    "pip install h5py==3.7.0",
    "pip install idna==3.4",
    "pip install imageio==2.9.0",
    "pip install importlib_metadata==8.4.0",
    "pip install importlib_resources==6.4.4",
    "pip install ipykernel==6.29.5",
    "pip install ipython==7.34.0",
    "pip install ipython-genutils==0.2.0",
    "pip install ipywidgets==7.7.2",
    "pip install itsdangerous==2.0.1",
    "pip install jedi==0.18.1",
    "pip install Jinja2==3.0.3",
    "pip install jsonschema==4.23.0",
    "pip install jsonschema-specifications==2023.12.1",
    "pip install jupyter-server==1.24.0",
    "pip install jupyter_client==7.4.9",
    "pip install jupyter_core==5.7.2",
    "pip install jupyterlab-widgets==1.0.0",
    "pip install jupyterlab_pygments==0.3.0",
    "pip install kiwisolver==1.3.2",
    "pip install lazy_loader==0.2",
    "pip install MarkupSafe==2.1.3",
    "pip install matplotlib==3.5.3",
    "pip install matplotlib-inline==0.1.6",
    "pip install mistune==3.0.2",
    "pip install mpmath==1.2.1",
    "pip install nbclassic==1.1.0",
    "pip install nbclient==0.10.0",
    "pip install nbconvert==7.16.4",
    "pip install nbformat==5.10.4",
    "pip install nest-asyncio==1.6.0",
    "pip install networkx==2.6.3",
    "pip install notebook==6.5.7",
    "pip install notebook_shim==0.2.4",
    "pip install numpy==1.21.6",
    "pip install opencv-python==4.6.0.66",
    "pip install packaging==21.3",
    "pip install pandocfilters==1.5.1",
    "pip install parso==0.8.3",
    "pip install pexpect==4.8.0",
    "pip install pickleshare==0.7.5",
    "pip install Pillow==9.0.1",
    "pip install pkgutil_resolve_name==1.3.10",
    "pip install platformdirs==4.2.2",
    "pip install prometheus_client==0.20.0",
    "pip install prompt-toolkit==3.0.36",
    "pip install psutil==6.0.0",
    "pip install ptyprocess==0.7.0",
    "pip install pure-eval==0.2.2",
    "pip install pycparser==2.22",
    "pip install Pygments==2.13.0",
    "pip install pyparsing==3.0.9",
    "pip install python-dateutil==2.8.2",
    "pip install python-engineio==4.3.4",
    "pip install python-socketio==5.3.0",
    "pip install PyWavelets==1.4.1",
    "pip install PyYAML==6.0",
    "pip install pyzmq==26.2.0",
    "pip install referencing==0.35.1",
    "pip install requests==2.28.2",
    "pip install rpds-py==0.20.0",
    "pip install scikit-image==0.19.3",
    "pip install scipy==1.7.3",
    "pip install Send2Trash==1.8.3",
    "pip install simple-websocket==0.3.0",
    "pip install six==1.16.0",
    "pip install sniffio==1.3.1",
    "pip install soupsieve==2.6",
    "pip install SQLAlchemy==1.4.47",
    "pip install stack-data==0.6.2",
    "pip install sympy==1.10.1",
    "pip install terminado==0.18.1",
    "pip install tifffile==2021.11.2",
    "pip install tinycss2==1.3.0",
    "pip install torch==1.13.1",
    "pip install tornado==6.4.1",
    "pip install traitlets==5.4.0",
    "pip install typing_extensions==4.4.0",
    "pip install urllib3==1.26.14",
    "pip install wcwidth==0.2.5",
    "pip install webencodings==0.5.1",
    "pip install websocket-client==1.8.0",
    "pip install Werkzeug==2.2.2",
    "pip install widgetsnbextension==3.6.4",
    "pip install wsproto==1.0.0",
    "pip install zipp==3.20.1",
    "pip install unav==0.1.40",
)

@app.function(image=custom_image)
@modal.wsgi_app()
def run_server():
    flask_app.debug = True
    return flask_app


# @app.local_entrypoint()
# def main():
#     run_server()
# socketio.run(
#         flask_app, host="0.0.0.0", port=5001, debug=True, use_reloader=False
#     )
