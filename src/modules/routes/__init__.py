from .auth_routes import register_auth_routes
from .data_routes import register_data_routes
from .frame_routes import register_frame_routes
from .update_routes import register_update_routes
from flask import render_template, request

def register_routes(app, server, socketio):
    register_auth_routes(app , socketio)
    register_data_routes(app, server, socketio)
    register_frame_routes(app, server, socketio)
    register_update_routes(app, server)

    @app.route('/')
    def index():
        return render_template('main.html')

    @app.route('/monitor')
    def monitor():
        return render_template('sub/monitor.html')

    @app.route('/floorplan')
    def floorplan():
        session_id = request.args.get('session_id')
        if session_id:
            return render_template('sub/floorplan.html', session_id=session_id)
        else:
            return "Session ID not provided", 400