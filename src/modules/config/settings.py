import yaml
from datetime import timedelta  # Import timedelta from datetime module

def load_config(filepath):
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)
    
class Config:
    SECRET_KEY = 'ai4celab'
    SQLALCHEMY_DATABASE_URI = 'sqlite:////mnt/data/UNav-IO/users/users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'unav.nyu@gmail.com'
    MAIL_PASSWORD = 'edeh wbec qfcp eddw'
    MAIL_DEFAULT_SENDER = 'unav.nyu@gmail.com'
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = '/tmp/flask_session/'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
