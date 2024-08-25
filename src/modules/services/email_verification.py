from flask import url_for, render_template, jsonify
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from ..db import db, User

class EmailVerification:
    def __init__(self, app, socketio):
        self.mail = Mail(app)
        self.serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        self.socketio = socketio

    def send_verification_email(self, email, username, hashed_password):
        token = self.serializer.dumps({'email': email, 'username': username, 'password_hash': hashed_password}, salt='email-confirm-salt')
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('email_confirmation.html', confirm_url=confirm_url)

        msg = Message(subject="Please confirm your email", recipients=[email])
        msg.html = html
        self.mail.send(msg)

    def confirm_token(self, token, expiration=300):
        try:
            data = self.serializer.loads(token, salt='email-confirm-salt', max_age=expiration)
        except Exception as e:
            return None
        return data

    def handle_confirmation(self, token):
        data = self.confirm_token(token)
        if not data:
            return render_template('registration/confirmation_error.html'), 400

        email = data['email']
        username = data['username']
        password_hash = data['password_hash']

        user = User.query.filter_by(email=email).first()
        if user:
            if user.email_confirmed:
                return render_template('registration/confirmation_already_verified.html'), 200
            else:
                user.email_confirmed = True
                db.session.commit()
                self.socketio.emit('registration_success', {'email': email, 'username': username})
                return render_template('registration/confirmation_success.html'), 200
        else:
            new_user = User(username=username, email=email, password_hash=password_hash, email_confirmed=True)
            db.session.add(new_user)
            db.session.commit()
            self.socketio.emit('registration_success', {'email': email, 'username': username})
            return render_template('registration/confirmation_success.html'), 200
