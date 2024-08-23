import logging

# SocketIOHandler to emit logs to the web client
class SocketIOHandler(logging.Handler):
    def __init__(self, socketio):
        super().__init__()
        self.socketio = socketio

    def emit(self, record):
        log_entry = self.format(record)
        self.socketio.emit('log', {'data': log_entry})

# Configure the logging system
def configure_logging(socketio):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not any(isinstance(handler, SocketIOHandler) for handler in logger.handlers):
        socketio_handler = SocketIOHandler(socketio)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        socketio_handler.setFormatter(formatter)
        logger.addHandler(socketio_handler)
