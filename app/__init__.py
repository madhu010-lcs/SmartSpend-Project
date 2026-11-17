
"""SmartSpend application factory."""

import os

from flask import Flask

from .extensions import db, login_manager


def create_app(config=None):
    app = Flask(__name__)

    uri = os.environ.get("DATABASE_URL", "sqlite:///smartspend.db")

    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI=uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CURRENCY="₹",
    )

    if config:
        app.config.update(config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from . import models  # noqa: F401
    from .routes import auth_bp, main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.cli.command("init-db")
    def init_db():
        """Initialize database tables."""
        db.create_all()
        print("Database tables created.")

    return app
