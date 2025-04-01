import pytest
from backend.document_verification import DocumentVerification
import os
from datetime import datetime

@pytest.fixture
def doc_verifier():
    """Provide a document verification instance"""
    return DocumentVerification()

@pytest.fixture
def sample_aadhaar_number():
    """Provide a sample Aadhaar number"""
    return '123456789012'

@pytest.fixture
def sample_auth_code():
    """Provide a sample DigiLocker auth code"""
    return 'test_auth_code_12345'

def test_digilocker_auth_url_generation(doc_verifier):
    """Test DigiLocker authorization URL generation"""
    auth_url = doc_verifier.generate_digilocker_auth_url()
    
    # Check URL structure
    assert auth_url.startswith('https://api.digitallocker.gov.in/public/oauth2/1/authorize')
    assert 'client_id=' in auth_url
    assert 'redirect_uri=' in auth_url
    assert 'response_type=code' in auth_url
    assert 'state=' in auth_url

def test_digilocker_callback_handling(doc_verifier, sample_auth_code, mock_digilocker):
    """Test DigiLocker callback handling"""
    success, documents = doc_verifier.handle_digilocker_callback(sample_auth_code)
    
    assert success == True
    assert 'aadhaar' in documents
    assert 'pan' in documents
    
    # Check document data structure
    aadhaar_data = documents['aadhaar']
    assert 'number' in aadhaar_data
    
    pan_data = documents['pan']
    assert 'number' in pan_data

def test_ekyc_initiation(doc_verifier, sample_aadhaar_number, mock_ekyc):
    """Test eKYC initiation"""
    success, response = doc_verifier.initiate_ekyc(sample_aadhaar_number)
    
    assert success == True
    assert 'request_id' in response
    assert response['otp_sent'] == True

def test_ekyc_otp_verification(doc_verifier, mock_ekyc):
    """Test eKYC OTP verification"""
    request_id = 'test_request_id'
    otp = '123456'
    
    success, response = doc_verifier.verify_ekyc_otp(request_id, otp)
    
    assert success == True
    assert 'verified' in response
    assert 'name' in response
    assert 'address' in response

def test_bank_statement_verification(doc_verifier, tmp_path):
    """Test bank statement verification"""
    # Create a sample PDF file
    file_path = tmp_path / "bank_statement.pdf"
    with open(file_path, 'w') as f:
        f.write("Sample bank statement content")
    
    success, analysis = doc_verifier.verify_bank_statement(str(file_path))
    
    assert success == True
    assert 'verified' in analysis
    assert 'average_balance' in analysis
    assert 'monthly_credits' in analysis
    assert 'salary_credits_found' in analysis

def test_salary_slip_verification(doc_verifier, tmp_path):
    """Test salary slip verification"""
    # Create a sample PDF file
    file_path = tmp_path / "salary_slip.pdf"
    with open(file_path, 'w') as f:
        f.write("Sample salary slip content")
    
    success, analysis = doc_verifier.verify_salary_slip(str(file_path))
    
    assert success == True
    assert 'verified' in analysis
    assert 'gross_salary' in analysis
    assert 'net_salary' in analysis
    assert 'employer_verified' in analysis

def test_invalid_aadhaar_ekyc(doc_verifier):
    """Test eKYC with invalid Aadhaar number"""
    invalid_aadhaar = '123456'  # Invalid format
    success, response = doc_verifier.initiate_ekyc(invalid_aadhaar)
    
    assert success == False
    assert 'error' in response

def test_invalid_digilocker_auth_code(doc_verifier):
    """Test DigiLocker callback with invalid auth code"""
    invalid_auth_code = 'invalid_code'
    success, response = doc_verifier.handle_digilocker_callback(invalid_auth_code)
    
    assert success == False
    assert 'error' in response

def test_invalid_ekyc_otp(doc_verifier):
    """Test eKYC with invalid OTP"""
    request_id = 'test_request_id'
    invalid_otp = '12345'  # Invalid OTP
    success, response = doc_verifier.verify_ekyc_otp(request_id, invalid_otp)
    
    assert success == False
    assert 'error' in response

def test_invalid_document_file(doc_verifier, tmp_path):
    """Test verification with invalid document file"""
    # Create an invalid file
    file_path = tmp_path / "invalid.txt"
    with open(file_path, 'w') as f:
        f.write("Invalid document content")
    
    # Test bank statement verification
    success, response = doc_verifier.verify_bank_statement(str(file_path))
    assert success == False
    assert 'error' in response
    
    # Test salary slip verification
    success, response = doc_verifier.verify_salary_slip(str(file_path))
    assert success == False
    assert 'error' in response

def test_digilocker_token_handling(doc_verifier, mock_digilocker):
    """Test DigiLocker token handling"""
    auth_code = 'test_auth_code'
    token_data = doc_verifier._get_digilocker_token(auth_code)
    
    assert 'access_token' in token_data
    assert token_data['access_token'] == 'test_access_token'

def test_document_fetching(doc_verifier, mock_digilocker):
    """Test document fetching from DigiLocker"""
    access_token = 'test_access_token'
    
    # Test Aadhaar fetching
    aadhaar_data = doc_verifier._fetch_aadhaar(access_token)
    assert aadhaar_data is not None
    assert 'number' in aadhaar_data
    
    # Test PAN fetching
    pan_data = doc_verifier._fetch_pan(access_token)
    assert pan_data is not None
    assert 'number' in pan_data

def test_ekyc_data_processing(doc_verifier):
    """Test eKYC response data processing"""
    sample_data = {
        'aadhaar_number': '123456789012',
        'name': 'Test User',
        'dob': '1990-01-01',
        'gender': 'M',
        'address': {
            'street': 'Test Street',
            'city': 'Test City',
            'state': 'Test State',
            'pincode': '123456'
        },
        'photo_url': 'http://example.com/photo.jpg'
    }
    
    processed_data = doc_verifier._process_ekyc_data(sample_data)
    
    assert processed_data['verified'] == True
    assert processed_data['name'] == sample_data['name']
    assert processed_data['dob'] == sample_data['dob']
    assert processed_data['gender'] == sample_data['gender']
    assert 'address' in processed_data
    assert 'verification_timestamp' in processed_data