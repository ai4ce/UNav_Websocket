import logging
from flask_socketio import SocketIO

class SocketIOHandler(logging.Handler):
    def __init__(self, socketio):
        super().__init__()
        self.socketio = socketio

    def emit(self, record):
        log_entry = self.format(record)
        self.socketio.emit('log', {'data': log_entry})
