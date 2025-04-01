import json
import pytest
from datetime import datetime

def test_register(client):
    """Test user registration"""
    data = {
        'email': 'test@example.com',
        'password': 'Test@123',
        'name': 'Test User',
        'phone': '+919876543210'
    }
    
    response = client.post(
        '/api/auth/register',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    assert response.status_code == 201
    assert 'message' in response.json
    assert 'access_token' in response.json

def test_login(client):
    """Test user login"""
    # First register a user
    register_data = {
        'email': 'test@example.com',
        'password': 'Test@123',
        'name': 'Test User'
    }
    client.post(
        '/api/auth/register',
        data=json.dumps(register_data),
        content_type='application/json'
    )
    
    # Try logging in
    login_data = {
        'email': 'test@example.com',
        'password': 'Test@123'
    }
    response = client.post(
        '/api/auth/login',
        data=json.dumps(login_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_submit_loan_application(client, auth_headers, sample_loan_application):
    """Test loan application submission"""
    response = client.post(
        '/api/loan/apply',
        data=json.dumps(sample_loan_application),
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert 'application_id' in response.json
    assert 'message' in response.json

def test_get_application_status(client, auth_headers, sample_loan_application):
    """Test getting application status"""
    # First submit an application
    response = client.post(
        '/api/loan/apply',
        data=json.dumps(sample_loan_application),
        headers=auth_headers
    )
    application_id = response.json['application_id']
    
    # Get application status
    response = client.get(
        f'/api/loan/application/{application_id}',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert 'status' in response.json
    assert 'approved_amount' in response.json
    assert 'interest_rate' in response.json

def test_document_upload(client, auth_headers):
    """Test document upload"""
    from io import BytesIO
    
    # Create a test file
    file_data = BytesIO(b'Test file content')
    
    data = {
        'document_type': 'bank_statement',
        'file': (file_data, 'test.pdf')
    }
    
    response = client.post(
        '/api/document/upload',
        data=data,
        headers={
            'Authorization': auth_headers['Authorization'],
            'Content-Type': 'multipart/form-data'
        }
    )
    
    assert response.status_code == 201
    assert 'document_id' in response.json
    assert 'message' in response.json

def test_create_payment_order(client, auth_headers, mock_razorpay):
    """Test payment order creation"""
    data = {
        'application_id': 1
    }
    
    response = client.post(
        '/api/payment/create-order',
        data=json.dumps(data),
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert 'order_id' in response.json
    assert 'amount' in response.json
    assert response.json['amount'] == 120  # Report fee

def test_verify_payment(client, auth_headers, mock_razorpay):
    """Test payment verification"""
    data = {
        'razorpay_order_id': 'test_order_id',
        'razorpay_payment_id': 'test_payment_id',
        'razorpay_signature': 'test_signature'
    }
    
    response = client.post(
        '/api/payment/verify',
        data=json.dumps(data),
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert 'message' in response.json
    assert 'payment_id' in response.json

def test_invalid_login(client):
    """Test login with invalid credentials"""
    data = {
        'email': 'wrong@example.com',
        'password': 'WrongPassword'
    }
    
    response = client.post(
        '/api/auth/login',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    assert response.status_code == 401
    assert 'error' in response.json

def test_protected_route_without_token(client):
    """Test accessing protected route without token"""
    response = client.get('/api/loan/application/1')
    
    assert response.status_code == 401
    assert 'error' in response.json

def test_invalid_loan_application(client, auth_headers):
    """Test submitting invalid loan application"""
    # Missing required fields
    data = {
        'full_name': 'Test User'
    }
    
    response = client.post(
        '/api/loan/apply',
        data=json.dumps(data),
        headers=auth_headers
    )
    
    assert response.status_code == 422
    assert 'error' in response.json

def test_document_upload_invalid_type(client, auth_headers):
    """Test uploading document with invalid type"""
    from io import BytesIO
    
    # Create a test file
    file_data = BytesIO(b'Test file content')
    
    data = {
        'document_type': 'invalid_type',
        'file': (file_data, 'test.txt')
    }
    
    response = client.post(
        '/api/document/upload',
        data=data,
        headers={
            'Authorization': auth_headers['Authorization'],
            'Content-Type': 'multipart/form-data'
        }
    )
    
    assert response.status_code == 400
    assert 'error' in response.json

def test_payment_verification_invalid_signature(client, auth_headers):
    """Test payment verification with invalid signature"""
    data = {
        'razorpay_order_id': 'test_order_id',
        'razorpay_payment_id': 'test_payment_id',
        'razorpay_signature': 'invalid_signature'
    }
    
    response = client.post(
        '/api/payment/verify',
        data=json.dumps(data),
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert 'error' in response.json