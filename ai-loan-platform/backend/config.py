import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///loan_app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-here')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    
    # File Upload
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    
    # DigiLocker
    DIGILOCKER_BASE_URL = os.getenv('DIGILOCKER_BASE_URL', 'https://api.digitallocker.gov.in/public/oauth2/1/')
    DIGILOCKER_CLIENT_ID = os.getenv('DIGILOCKER_CLIENT_ID')
    DIGILOCKER_CLIENT_SECRET = os.getenv('DIGILOCKER_CLIENT_SECRET')
    DIGILOCKER_REDIRECT_URI = os.getenv('DIGILOCKER_REDIRECT_URI')
    
    # eKYC
    EKYC_BASE_URL = os.getenv('EKYC_BASE_URL')
    EKYC_API_KEY = os.getenv('EKYC_API_KEY')
    
    # Razorpay
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
    REPORT_FEE = 120  # ₹120
    
    # AI Model
    MODEL_WEIGHTS_PATH = 'models/loan_assessment_model.pkl'
    
    # Report Generation
    REPORT_FOLDER = 'reports'
    
    # CORS
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:8000']
    
    # Security
    PASSWORD_SALT = os.getenv('PASSWORD_SALT', 'your-salt-here')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'logs/app.log'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Override with production values
    CORS_ORIGINS = ['https://yourdomain.com']
    
    # Stricter security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Production logging
    LOG_LEVEL = 'ERROR'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Mock external services
    DIGILOCKER_BASE_URL = 'http://mock-digilocker-api'
    EKYC_BASE_URL = 'http://mock-ekyc-api'

# Dictionary for easy config selection
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration class based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])