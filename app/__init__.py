"""SmartSpend application factory."""
import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config=None):
    app = Flask(__name__)

    uri = os.environ.get("DATABASE_URL", "sqlite:///smartspend.db")
    if uri.startswith("postgres://"):  # Render / Heroku style URL
        uri = uri.replace("postgres://", "postgresql://", 1)

    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        SQLALCHEMY_DATABASE_URI=uri,
        ALERT_THRESHOLD=float(os.environ.get("ALERT_THRESHOLD", "0.8")),
        CURRENCY="\u20b9",
    )
    if config:
        app.config.update(config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Log in to see your expenses."
    csrf.init_app(app)

    from . import models  # noqa: F401  (registers tables and user loader)
    from .routes import auth_bp, main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app
