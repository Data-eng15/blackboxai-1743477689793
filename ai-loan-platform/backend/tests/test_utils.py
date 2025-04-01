import pytest
from datetime import date, datetime
from backend.utils import (
    validate_email, validate_phone, validate_aadhaar, validate_pan,
    validate_pincode, calculate_age, format_currency, calculate_emi,
    allowed_file, validate_loan_application, mask_aadhaar, mask_pan
)

def test_email_validation():
    """Test email validation"""
    assert validate_email('test@example.com') == True
    assert validate_email('test.user@example.co.in') == True
    assert validate_email('test@example') == False
    assert validate_email('test@.com') == False
    assert validate_email('test.com') == False
    assert validate_email('@example.com') == False

def test_phone_validation():
    """Test phone number validation"""
    assert validate_phone('+919876543210') == True
    assert validate_phone('919876543210') == True
    assert validate_phone('9876543210') == True
    assert validate_phone('123') == False
    assert validate_phone('abcdefghijk') == False
    assert validate_phone('+91987654321a') == False

def test_aadhaar_validation():
    """Test Aadhaar number validation"""
    assert validate_aadhaar('123456789012') == True
    assert validate_aadhaar('12345678901') == False
    assert validate_aadhaar('1234567890123') == False
    assert validate_aadhaar('abcdefghijkl') == False

def test_pan_validation():
    """Test PAN number validation"""
    assert validate_pan('ABCDE1234F') == True
    assert validate_pan('AAAAA1111A') == True
    assert validate_pan('12345ABCDE') == False
    assert validate_pan('ABCD12345') == False
    assert validate_pan('ABCDE123456') == False

def test_pincode_validation():
    """Test pincode validation"""
    assert validate_pincode('123456') == True
    assert validate_pincode('12345') == False
    assert validate_pincode('1234567') == False
    assert validate_pincode('abcdef') == False

def test_age_calculation():
    """Test age calculation"""
    today = date.today()
    
    # Test with different dates
    assert calculate_age(date(1990, 1, 1)) == today.year - 1990
    assert calculate_age(date(2000, 12, 31)) == today.year - 2000
    
    # Test with future date
    future_date = date(today.year + 1, 1, 1)
    assert calculate_age(future_date) == -1
    
    # Test with today's date
    assert calculate_age(today) == 0

def test_currency_formatting():
    """Test currency formatting"""
    assert format_currency(1000) == '₹1,000.00'
    assert format_currency(1000.50) == '₹1,000.50'
    assert format_currency(1000000) == '₹1,000,000.00'
    assert format_currency(0) == '₹0.00'
    assert format_currency(0.99) == '₹0.99'

def test_emi_calculation():
    """Test EMI calculation"""
    # Test with sample loan data
    principal = 100000  # ₹1 lakh
    rate = 12  # 12% per annum
    tenure = 12  # 1 year
    
    emi = calculate_emi(principal, rate, tenure)
    
    # EMI should be positive
    assert emi > 0
    # EMI * tenure should be greater than principal (due to interest)
    assert emi * tenure > principal
    
    # Test with zero values
    assert calculate_emi(0, rate, tenure) == 0
    assert calculate_emi(principal, 0, tenure) > 0

def test_allowed_file():
    """Test file extension validation"""
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png'}
    
    assert allowed_file('document.pdf', allowed_extensions) == True
    assert allowed_file('image.jpg', allowed_extensions) == True
    assert allowed_file('image.jpeg', allowed_extensions) == True
    assert allowed_file('image.png', allowed_extensions) == True
    assert allowed_file('document.doc', allowed_extensions) == False
    assert allowed_file('file.txt', allowed_extensions) == False
    assert allowed_file('noextension', allowed_extensions) == False

def test_loan_application_validation():
    """Test loan application validation"""
    # Valid application data
    valid_data = {
        'full_name': 'Test User',
        'date_of_birth': '1990-01-01',
        'pan_number': 'ABCDE1234F',
        'aadhaar_number': '123456789012',
        'phone': '+919876543210',
        'address_line1': 'Test Street',
        'city': 'Test City',
        'state': 'Test State',
        'pincode': '123456',
        'employment_type': 'full_time',
        'monthly_income': 50000,
        'loan_amount': 500000,
        'loan_tenure': 24
    }
    
    errors = validate_loan_application(valid_data)
    assert len(errors) == 0
    
    # Test missing required fields
    invalid_data = valid_data.copy()
    invalid_data.pop('full_name')
    errors = validate_loan_application(invalid_data)
    assert len(errors) > 0
    assert 'full_name is required' in errors
    
    # Test invalid formats
    invalid_data = valid_data.copy()
    invalid_data['email'] = 'invalid-email'
    invalid_data['phone'] = '123'
    invalid_data['pan_number'] = '123456'
    errors = validate_loan_application(invalid_data)
    assert len(errors) > 0
    assert 'Invalid email format' in errors
    assert 'Invalid phone number format' in errors
    assert 'Invalid PAN number format' in errors

def test_masking_functions():
    """Test Aadhaar and PAN masking"""
    # Test Aadhaar masking
    assert mask_aadhaar('123456789012') == 'XXXX-XXXX-9012'
    assert len(mask_aadhaar('123456789012')) == 14
    
    # Test PAN masking
    assert mask_pan('ABCDE1234F') == 'AB****234F'
    assert len(mask_pan('ABCDE1234F')) == 10