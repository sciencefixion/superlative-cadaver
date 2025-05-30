from flask import Flask
from .extensions import db

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///games.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    db.init_app(app)

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app