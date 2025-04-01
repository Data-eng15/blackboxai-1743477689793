import pytest
from backend import create_app
from backend.models import db as _db
import os
import tempfile

@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask application"""
    # Create a temporary file for SQLite database
    db_fd, db_path = tempfile.mkstemp()
    
    # Test configuration
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-jwt-secret-key',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'UPLOAD_FOLDER': tempfile.mkdtemp(),
        'REPORT_FOLDER': tempfile.mkdtemp(),
    }
    
    # Create app with test config
    app = create_app()
    app.config.update(test_config)
    
    # Create context and database tables
    with app.app_context():
        _db.create_all()
    
    # Provide the app for testing
    yield app
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)
    os.rmdir(app.config['UPLOAD_FOLDER'])
    os.rmdir(app.config['REPORT_FOLDER'])

@pytest.fixture(scope='session')
def db(app):
    """Provide the database for testing"""
    with app.app_context():
        yield _db
        _db.drop_all()

@pytest.fixture(scope='function')
def session(db):
    """Provide a database session for testing"""
    connection = db.engine.connect()
    transaction = connection.begin()
    session = db.create_scoped_session(
        options={'bind': connection, 'binds': {}}
    )
    db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def client(app):
    """Provide a test client"""
    return app.test_client()

@pytest.fixture
def auth_headers(app, client):
    """Provide authentication headers for protected routes"""
    from flask_jwt_extended import create_access_token
    
    # Create a test user
    with app.app_context():
        access_token = create_access_token(identity=1)
    
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

@pytest.fixture
def mock_razorpay(monkeypatch):
    """Mock Razorpay API calls"""
    class MockRazorpay:
        def __init__(self, *args, **kwargs):
            pass
        
        def order(self):
            class MockOrder:
                @staticmethod
                def create(data):
                    return {
                        'id': 'test_order_id',
                        'amount': data['amount'],
                        'currency': data['currency'],
                        'receipt': data['receipt']
                    }
            return MockOrder()
        
        def payment(self):
            class MockPayment:
                @staticmethod
                def fetch(payment_id):
                    return {
                        'id': payment_id,
                        'order_id': 'test_order_id',
                        'amount': 12000,
                        'status': 'captured',
                        'method': 'card',
                        'created_at': 1630000000
                    }
            return MockPayment()
    
    monkeypatch.setattr('razorpay.Client', MockRazorpay)

@pytest.fixture
def mock_digilocker(monkeypatch):
    """Mock DigiLocker API calls"""
    def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
            
            def json(self):
                return {
                    'access_token': 'test_access_token',
                    'documents': {
                        'aadhaar': {'number': '123456789012'},
                        'pan': {'number': 'ABCDE1234F'}
                    }
                }
        return MockResponse()
    
    monkeypatch.setattr('requests.get', mock_get)
    monkeypatch.setattr('requests.post', mock_get)

@pytest.fixture
def mock_ekyc(monkeypatch):
    """Mock eKYC API calls"""
    def mock_post(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
            
            def json(self):
                return {
                    'request_id': 'test_request_id',
                    'status': 'success',
                    'data': {
                        'name': 'Test User',
                        'dob': '1990-01-01',
                        'gender': 'M',
                        'address': {
                            'street': 'Test Street',
                            'city': 'Test City',
                            'state': 'Test State',
                            'pincode': '123456'
                        }
                    }
                }
        return MockResponse()
    
    monkeypatch.setattr('requests.post', mock_post)

@pytest.fixture
def sample_loan_application():
    """Provide sample loan application data"""
    return {
        'full_name': 'Test User',
        'date_of_birth': '1990-01-01',
        'pan_number': 'ABCDE1234F',
        'aadhaar_number': '123456789012',
        'phone': '+919876543210',
        'email': 'test@example.com',
        'address_line1': 'Test Street',
        'city': 'Test City',
        'state': 'Test State',
        'pincode': '123456',
        'employment_type': 'full_time',
        'employer_name': 'Test Company',
        'monthly_income': 50000,
        'work_experience': 5,
        'loan_amount': 500000,
        'loan_purpose': 'personal',
        'loan_tenure': 24
    }