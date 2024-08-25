from flask_sqlalchemy import SQLAlchemy

# Initialize the database connection
db = SQLAlchemy()

def init_db(app):
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app

# Define models here
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(150), nullable=False)
    email_confirmed = db.Column(db.Boolean, default=False)
