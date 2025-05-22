from flask import Flask
from .db import db

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.config.Development')  # Load development config by default

    db.init_app(app)

    with app.app_context():
        # Import blueprints 
        from .auth import routes
        db.create_all()  #  create tables if not exist

    return app
