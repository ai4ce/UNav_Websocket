import yaml
from datetime import timedelta  # Import timedelta from datetime module
import os

# Get the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))


def load_config(filepath=None):
    if filepath is None:
        print("No configuration file path provided.")
        filepath = os.path.join(os.path.dirname(__file__), "default_config.yaml")
        print("default file path:", filepath)
        
    with open(filepath, "r") as f:
        return yaml.safe_load(f)


class Config:
    SECRET_KEY = "ai4celab"
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(current_directory, "users.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = "unav.nyu@gmail.com"
    MAIL_PASSWORD = "edeh wbec qfcp eddw"
    MAIL_DEFAULT_SENDER = "unav.nyu@gmail.com"
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = "/tmp/flask_session/"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
