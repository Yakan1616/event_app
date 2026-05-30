"""Application factory"""

from flask import Flask
from flask_wtf.csrf import CSRFProtect
import app.models as models
from app.routes.auth import auth_bp
from app.routes.events import events_bp
from config import config

csrf = CSRFProtect()

def create_app(config_name="development"):
    """Create and configure the Flask application"""
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, "templates"),
                static_folder=os.path.join(base_dir, "static"))
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Initialize database
    models.init_db(app.config["DATABASE_URL"])
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(events_bp)
    
    return app
