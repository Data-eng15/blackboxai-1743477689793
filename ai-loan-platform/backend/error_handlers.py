from flask import Blueprint, jsonify
from werkzeug.exceptions import HTTPException
import logging
import traceback
from datetime import datetime
import os

# Initialize blueprint
errors = Blueprint('errors', __name__)

# Configure logging
def setup_logging(app):
    """Configure application logging"""
    log_folder = 'logs'
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    
    log_file = os.path.join(log_folder, 'app.log')
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(app.config['LOG_LEVEL'])

# Error handlers
@errors.app_errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions"""
    # Log the error
    app = errors.app
    app.logger.error(f'Unhandled Exception: {str(e)}')
    app.logger.error(traceback.format_exc())
    
    # Return error response
    if isinstance(e, HTTPException):
        return jsonify({
            'error': {
                'code': e.code,
                'name': e.name,
                'description': e.description,
            }
        }), e.code
    
    # Production error message
    if app.config['DEBUG']:
        error_details = str(e)
    else:
        error_details = 'An unexpected error occurred'
    
    return jsonify({
        'error': {
            'code': 500,
            'name': 'Internal Server Error',
            'description': error_details
        }
    }), 500

@errors.app_errorhandler(400)
def bad_request_error(e):
    """Handle bad request errors"""
    return jsonify({
        'error': {
            'code': e.code,
            'name': 'Bad Request',
            'description': str(e.description)
        }
    }), 400

@errors.app_errorhandler(401)
def unauthorized_error(e):
    """Handle unauthorized access errors"""
    return jsonify({
        'error': {
            'code': e.code,
            'name': 'Unauthorized',
            'description': 'Authentication is required to access this resource'
        }
    }), 401

@errors.app_errorhandler(403)
def forbidden_error(e):
    """Handle forbidden access errors"""
    return jsonify({
        'error': {
            'code': e.code,
            'name': 'Forbidden',
            'description': 'You do not have permission to access this resource'
        }
    }), 403

@errors.app_errorhandler(404)
def not_found_error(e):
    """Handle not found errors"""
    return jsonify({
        'error': {
            'code': e.code,
            'name': 'Not Found',
            'description': 'The requested resource was not found'
        }
    }), 404

@errors.app_errorhandler(405)
def method_not_allowed_error(e):
    """Handle method not allowed errors"""
    return jsonify({
        'error': {
            'code': e.code,
            'name': 'Method Not Allowed',
            'description': 'The method is not allowed for this resource'
        }
    }), 405

@errors.app_errorhandler(422)
def validation_error(e):
    """Handle validation errors"""
    return jsonify({
        'error': {
            'code': e.code,
            'name': 'Unprocessable Entity',
            'description': 'The request data failed validation',
            'errors': e.data.get('messages', {}) if hasattr(e, 'data') else None
        }
    }), 422

@errors.app_errorhandler(429)
def ratelimit_error(e):
    """Handle rate limit exceeded errors"""
    return jsonify({
        'error': {
            'code': e.code,
            'name': 'Too Many Requests',
            'description': 'Rate limit exceeded. Please try again later'
        }
    }), 429

class APIError(Exception):
    """Base class for API errors"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = {
            'error': {
                'code': self.status_code,
                'message': self.message
            }
        }
        if self.payload:
            rv['error']['details'] = self.payload
        return rv

@errors.app_errorhandler(APIError)
def handle_api_error(e):
    """Handle custom API errors"""
    return jsonify(e.to_dict()), e.status_code

# Custom error classes
class ValidationError(APIError):
    """Raised when request data fails validation"""
    def __init__(self, message, errors=None):
        super().__init__(message, status_code=422, payload={'validation_errors': errors})

class ResourceNotFoundError(APIError):
    """Raised when a requested resource is not found"""
    def __init__(self, message):
        super().__init__(message, status_code=404)

class AuthenticationError(APIError):
    """Raised when authentication fails"""
    def __init__(self, message):
        super().__init__(message, status_code=401)

class AuthorizationError(APIError):
    """Raised when user lacks permission"""
    def __init__(self, message):
        super().__init__(message, status_code=403)

class PaymentError(APIError):
    """Raised when payment processing fails"""
    def __init__(self, message, payment_details=None):
        super().__init__(message, status_code=400, payload={'payment_details': payment_details})

class DocumentVerificationError(APIError):
    """Raised when document verification fails"""
    def __init__(self, message, verification_details=None):
        super().__init__(message, status_code=400, payload={'verification_details': verification_details})

def init_app(app):
    """Initialize error handlers with the Flask app"""
    app.register_blueprint(errors)
    setup_logging(app)