import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    slug = "spend_analytics"
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(32).hex())
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_NAME"] = f"{slug}_session"
    app.config["SESSION_COOKIE_PATH"] = os.environ.get("SESSION_COOKIE_PATH", "/")
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["WTF_CSRF_TIME_LIMIT"] = None

    logging.basicConfig(level=logging.INFO)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    migrate.init_app(app, db)
    csrf.init_app(app)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.spend import spend_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.contracts import contracts_bp
    from app.routes.analysis import analysis_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    from app.routes.getting_started import gs_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(spend_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(contracts_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(gs_bp)

    with app.app_context():
        db.create_all()
        _seed_defaults(app)

    return app


def _seed_defaults(app):
    from app.models import User, Tenant, Role
    if Tenant.query.first():
        return
    t = Tenant(name="Default Organization", slug="default")
    db.session.add(t)
    db.session.flush()
    for rname in ["admin", "analyst", "viewer"]:
        db.session.add(Role(name=rname, tenant_id=t.id))
    db.session.flush()
    admin_role = Role.query.filter_by(name="admin", tenant_id=t.id).first()
    u = User(username="admin", email="admin@example.com", tenant_id=t.id, role_id=admin_role.id, is_active=True)
    u.set_password("admin")
    db.session.add(u)
    db.session.commit()
