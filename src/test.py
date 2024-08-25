from flask import Flask, session, jsonify, redirect, url_for
from flask_session import Session

app = Flask(__name__)

# Configuration for the session storage
app.config['SECRET_KEY'] = 'asfadf'
app.config['SESSION_TYPE'] = 'filesystem'  # To use filesystem-based sessions
app.config['SESSION_FILE_DIR'] = '/tmp/flask_session/'  # Directory to store session files
app.config['SESSION_PERMANENT'] = False  # Session should not be permanent
app.config['SESSION_USE_SIGNER'] = True  # Adds an extra layer of security to cookies

# Initialize the session
Session(app)


@app.route('/')
def index():
    # Show the session data
    return jsonify(session_data=dict(session))


@app.route('/set_session')
def set_session():
    # Set some data in the session
    session['username'] = 'test_user'
    session['email'] = 'test_user@example.com'
    session.modified = True  # Ensure session data is saved
    return jsonify(message='Session data set', session_data=dict(session))


@app.route('/get_session')
def get_session():
    # Retrieve session data
    username = session.get('username', 'not set')
    email = session.get('email', 'not set')
    return jsonify(username=username, email=email)


@app.route('/clear_session')
def clear_session():
    # Clear the session data
    session.clear()
    return jsonify(message='Session cleared')


@app.route('/modify_session')
def modify_session():
    # Modify existing session data
    if 'username' in session:
        session['username'] = 'modified_user'
        session.modified = True  # Ensure session data is saved
        return jsonify(message='Session modified', session_data=dict(session))
    else:
        return jsonify(message='No session data to modify')


if __name__ == '__main__':
    app.run(debug=True)
