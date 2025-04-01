import pytest
from flask import Flask
from werkzeug.exceptions import NotFound, BadRequest, Unauthorized, Forbidden
from backend.error_handlers import (
    APIError, ValidationError, ResourceNotFoundError,
    AuthenticationError, AuthorizationError, PaymentError,
    DocumentVerificationError, setup_logging
)

@pytest.fixture
def app():
    """Create test Flask application"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

def test_generic_exception_handler(app, client):
    """Test handling of generic exceptions"""
    @app.route('/test-error')
    def test_error():
        raise Exception('Test error')
    
    response = client.get('/test-error')
    assert response.status_code == 500
    assert 'error' in response.json
    assert response.json['error']['code'] == 500
    assert 'Internal Server Error' in response.json['error']['name']

def test_http_exception_handlers(app, client):
    """Test handling of HTTP exceptions"""
    @app.route('/not-found')
    def not_found():
        raise NotFound()
    
    @app.route('/bad-request')
    def bad_request():
        raise BadRequest()
    
    @app.route('/unauthorized')
    def unauthorized():
        raise Unauthorized()
    
    @app.route('/forbidden')
    def forbidden():
        raise Forbidden()
    
    # Test 404
    response = client.get('/not-found')
    assert response.status_code == 404
    assert 'Not Found' in response.json['error']['name']
    
    # Test 400
    response = client.get('/bad-request')
    assert response.status_code == 400
    assert 'Bad Request' in response.json['error']['name']
    
    # Test 401
    response = client.get('/unauthorized')
    assert response.status_code == 401
    assert 'Unauthorized' in response.json['error']['name']
    
    # Test 403
    response = client.get('/forbidden')
    assert response.status_code == 403
    assert 'Forbidden' in response.json['error']['name']

def test_validation_error_handler(app, client):
    """Test handling of validation errors"""
    @app.route('/validate')
    def validate():
        errors = {'field1': 'Invalid value', 'field2': 'Required'}
        raise ValidationError('Validation failed', errors)
    
    response = client.get('/validate')
    assert response.status_code == 422
    assert 'Validation failed' in response.json['error']['message']
    assert 'validation_errors' in response.json['error']['details']

def test_resource_not_found_handler(app, client):
    """Test handling of resource not found errors"""
    @app.route('/resource')
    def get_resource():
        raise ResourceNotFoundError('Resource not found')
    
    response = client.get('/resource')
    assert response.status_code == 404
    assert 'Resource not found' in response.json['error']['message']

def test_authentication_error_handler(app, client):
    """Test handling of authentication errors"""
    @app.route('/auth')
    def authenticate():
        raise AuthenticationError('Invalid credentials')
    
    response = client.get('/auth')
    assert response.status_code == 401
    assert 'Invalid credentials' in response.json['error']['message']

def test_authorization_error_handler(app, client):
    """Test handling of authorization errors"""
    @app.route('/authorize')
    def authorize():
        raise AuthorizationError('Permission denied')
    
    response = client.get('/authorize')
    assert response.status_code == 403
    assert 'Permission denied' in response.json['error']['message']

def test_payment_error_handler(app, client):
    """Test handling of payment errors"""
    @app.route('/payment')
    def process_payment():
        payment_details = {'order_id': '123', 'error': 'Payment failed'}
        raise PaymentError('Payment processing failed', payment_details)
    
    response = client.get('/payment')
    assert response.status_code == 400
    assert 'Payment processing failed' in response.json['error']['message']
    assert 'payment_details' in response.json['error']['payload']

def test_document_verification_error_handler(app, client):
    """Test handling of document verification errors"""
    @app.route('/verify')
    def verify_document():
        details = {'document_type': 'aadhaar', 'error': 'Verification failed'}
        raise DocumentVerificationError('Document verification failed', details)
    
    response = client.get('/verify')
    assert response.status_code == 400
    assert 'Document verification failed' in response.json['error']['message']
    assert 'verification_details' in response.json['error']['payload']

def test_error_logging(app, tmp_path):
    """Test error logging setup and functionality"""
    # Configure logging with temporary directory
    log_file = tmp_path / 'app.log'
    app.config['LOG_FILE'] = str(log_file)
    setup_logging(app)
    
    # Generate some test errors
    with app.test_client() as client:
        @app.route('/test-log')
        def test_log():
            app.logger.error('Test error message')
            return 'OK'
        
        client.get('/test-log')
    
    # Check log file
    assert log_file.exists()
    log_content = log_file.read_text()
    assert 'Test error message' in log_content

def test_api_error_base_class():
    """Test base APIError class"""
    error = APIError('Test message', status_code=418, payload={'key': 'value'})
    error_dict = error.to_dict()
    
    assert error_dict['error']['code'] == 418
    assert error_dict['error']['message'] == 'Test message'
    assert error_dict['error']['details']['key'] == 'value'

def test_error_handler_in_production(app, client):
    """Test error handling in production mode"""
    app.config['DEBUG'] = False
    
    @app.route('/prod-error')
    def prod_error():
        raise Exception('Detailed error message')
    
    response = client.get('/prod-error')
    assert response.status_code == 500
    assert 'Detailed error message' not in response.json['error']['description']
    assert 'An unexpected error occurred' in response.json['error']['description']

def test_error_handler_in_debug_mode(app, client):
    """Test error handling in debug mode"""
    app.config['DEBUG'] = True
    
    @app.route('/debug-error')
    def debug_error():
        raise Exception('Detailed error message')
    
    response = client.get('/debug-error')
    assert response.status_code == 500
    assert 'Detailed error message' in response.json['error']['description']