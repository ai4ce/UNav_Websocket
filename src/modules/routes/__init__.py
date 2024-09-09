from .auth_routes import register_auth_routes
from .data_routes import register_data_routes
from .frame_routes import register_frame_routes
from .update_routes import register_update_routes
from flask import render_template
import os

templates_path = os.path.join(os.path.dirname(__file__), "templates")

def register_routes(app, server, socketio):
    register_auth_routes(app , socketio)
    register_data_routes(app, server)
    register_frame_routes(app, server, socketio)
    register_update_routes(app, server)

    @app.route('/')
    def index():
        # app.jinja_loader.searchpath = [templates_path]
        print(app.jinja_loader.searchpath)
        return render_template('main.html')

    @app.route('/monitor')
    def monitor():
        return render_template('sub/monitor.html')
