from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

from .config import get_config
from .models import db
from .routes import init_app as init_routes
from .error_handlers import init_app as init_error_handlers

def create_app(config_name=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)
    
    # Ensure required directories exist
    _create_required_directories(app)
    
    # Initialize extensions
    CORS(app, origins=app.config['CORS_ORIGINS'])
    JWTManager(app)
    db.init_app(app)
    
    # Initialize routes and error handlers
    init_routes(app)
    init_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

def _create_required_directories(app):
    """Create required directories for the application"""
    directories = [
        app.config['UPLOAD_FOLDER'],
        app.config['REPORT_FOLDER'],
        'logs'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])