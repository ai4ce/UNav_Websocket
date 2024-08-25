from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from modules.db import User
from ..services.email_verification import EmailVerification
import re

def validate_password(password):
    if len(password) < 10:
        return False, "Password must be at least 10 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        return False, "Password must contain at least one special character."
    return True, None

def register_auth_routes(app, socketio):
    email_verifier = EmailVerification(app, socketio)

    @app.route('/register', methods=['POST'])
    def register():
        data = request.json
        username, password, email = data.get('username'), data.get('password'), data.get('email')

        if not username or not password or not email:
            return jsonify({'error': 'Missing data'}), 400

        existing_user_by_username = User.query.filter_by(username=username).first()
        existing_user_by_email = User.query.filter_by(email=email).first()

        if existing_user_by_username:
            return jsonify({'error': 'Username already exists'}), 409

        if existing_user_by_email:
            return jsonify({'error': 'Email already exists'}), 409

        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400

        hashed_password = generate_password_hash(password)

        # Send verification email and store user data with token
        email_verifier.send_verification_email(email, username, hashed_password)

        return jsonify({'status': 'Please check your email to verify your account.'}), 201

    @app.route('/login', methods=['POST'])
    def login():
        data = request.json
        username, password = data.get('username'), data.get('password')

        if not username or not password:
            return jsonify({'error': 'Missing data'}), 400

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.email_confirmed:
                return jsonify({'error': 'Please verify your email before logging in.'}), 403
            return jsonify({'status': 'Login successful'})
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    @app.route('/logout', methods=['POST'])
    def logout():
        return jsonify({'status': 'Logged out successfully'})

    @app.route('/confirm/<token>', methods=['GET'])
    def confirm_email(token):
        return email_verifier.handle_confirmation(token)
