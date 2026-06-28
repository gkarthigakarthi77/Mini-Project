import os
from flask import Flask
from config import config_dict
from extensions import db, login_manager, csrf
from models import User
from utils.logger import log_action


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config_dict[config_name])

    # Ensure secret key is set
    if not app.config['SECRET_KEY'] or app.config['SECRET_KEY'] == 'dev-key-change-in-production':
        app.logger.warning('SECRET_KEY not set to a secure value!')

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.dashboard import dashboard_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    # ✅ Disable CSRF protection for API blueprint (JSON endpoints)
    csrf.exempt(api_bp)

    # Create tables
    with app.app_context():
        db.create_all()
        # Create admin user if none exists (for demo)
        if not User.query.filter_by(is_admin=True).first():
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('Admin123!'),
                is_admin=True,
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            app.logger.info('Created default admin user: admin@example.com / Admin123!')

    return app