import os

from flask import Flask, session

from .config import Config
from .extensions import db
from .models import Admin


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure folders required by SQLite and uploads exist.
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
        db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "", 1)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    db.init_app(app)

    from .routes.attendance import attendance_bp
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.employees import employees_bp
    from .routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)

    @app.context_processor
    def inject_current_admin():
        admin_id = session.get("admin_id")
        admin = db.session.get(Admin, admin_id) if admin_id else None
        return {"current_admin": admin}

    return app
