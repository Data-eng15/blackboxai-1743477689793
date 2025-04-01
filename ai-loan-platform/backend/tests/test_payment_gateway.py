import pytest
from backend.payment_gateway import PaymentGateway
from datetime import datetime

@pytest.fixture
def payment_gateway():
    """Provide a payment gateway instance"""
    return PaymentGateway()

@pytest.fixture
def sample_payment_data():
    """Provide sample payment data"""
    return {
        'razorpay_order_id': 'order_test123',
        'razorpay_payment_id': 'pay_test123',
        'razorpay_signature': 'valid_signature_hash'
    }

def test_order_creation(payment_gateway, mock_razorpay):
    """Test payment order creation"""
    user_id = 1
    application_id = 1
    
    success, order_data = payment_gateway.create_order(user_id, application_id)
    
    assert success == True
    assert 'order_id' in order_data
    assert 'amount' in order_data
    assert 'currency' in order_data
    assert 'receipt' in order_data
    
    # Check amount is correct (₹120)
    assert order_data['amount'] == 120
    assert order_data['currency'] == 'INR'

def test_payment_verification(payment_gateway, sample_payment_data, mock_razorpay):
    """Test payment verification"""
    success, verification_data = payment_gateway.verify_payment(sample_payment_data)
    
    assert success == True
    assert 'payment_id' in verification_data
    assert 'order_id' in verification_data
    assert 'amount' in verification_data
    assert 'status' in verification_data
    assert verification_data['status'] == 'captured'

def test_signature_verification(payment_gateway):
    """Test payment signature verification"""
    order_id = 'order_test123'
    payment_id = 'pay_test123'
    
    # Generate a valid signature
    valid_signature = payment_gateway._verify_signature(
        order_id,
        payment_id,
        'valid_signature_hash'
    )
    
    assert valid_signature == True

def test_refund_processing(payment_gateway, mock_razorpay):
    """Test payment refund processing"""
    payment_id = 'pay_test123'
    amount = 120
    
    success, refund_data = payment_gateway.refund_payment(payment_id, amount)
    
    assert success == True
    assert 'refund_id' in refund_data
    assert 'payment_id' in refund_data
    assert 'amount' in refund_data
    assert 'status' in refund_data
    assert refund_data['amount'] == amount

def test_payment_status_check(payment_gateway, mock_razorpay):
    """Test payment status checking"""
    payment_id = 'pay_test123'
    
    success, status_data = payment_gateway.get_payment_status(payment_id)
    
    assert success == True
    assert 'payment_id' in status_data
    assert 'order_id' in status_data
    assert 'amount' in status_data
    assert 'status' in status_data
    assert 'method' in status_data
    assert 'timestamp' in status_data

def test_receipt_generation(payment_gateway):
    """Test payment receipt generation"""
    payment_data = {
        'payment_id': 'pay_test123',
        'order_id': 'order_test123',
        'amount': 120,
        'payment_method': 'card',
        'application_id': 1
    }
    
    receipt_data = payment_gateway.generate_payment_receipt(payment_data)
    
    assert 'receipt_number' in receipt_data
    assert 'date' in receipt_data
    assert 'amount' in receipt_data
    assert 'payment_id' in receipt_data
    assert 'order_id' in receipt_data
    assert 'payment_method' in receipt_data
    assert 'description' in receipt_data
    assert 'status' in receipt_data
    assert 'customer_details' in receipt_data

def test_invalid_payment_verification(payment_gateway):
    """Test payment verification with invalid data"""
    invalid_payment_data = {
        'razorpay_order_id': 'invalid_order',
        'razorpay_payment_id': 'invalid_payment',
        'razorpay_signature': 'invalid_signature'
    }
    
    success, response = payment_gateway.verify_payment(invalid_payment_data)
    
    assert success == False
    assert 'error' in response

def test_invalid_refund_request(payment_gateway):
    """Test refund with invalid payment ID"""
    invalid_payment_id = 'invalid_payment'
    
    success, response = payment_gateway.refund_payment(invalid_payment_id)
    
    assert success == False
    assert 'error' in response

def test_zero_amount_order(payment_gateway):
    """Test creating order with zero amount"""
    user_id = 1
    application_id = 1
    
    # Override report fee to zero (should not be possible in real scenario)
    payment_gateway.report_fee = 0
    
    success, response = payment_gateway.create_order(user_id, application_id)
    
    assert success == False
    assert 'error' in response

def test_partial_refund(payment_gateway, mock_razorpay):
    """Test partial refund processing"""
    payment_id = 'pay_test123'
    partial_amount = 60  # Half of the report fee
    
    success, refund_data = payment_gateway.refund_payment(payment_id, partial_amount)
    
    assert success == True
    assert refund_data['amount'] == partial_amount
    assert refund_data['status'] in ['processed', 'pending']

def test_payment_status_transitions(payment_gateway, mock_razorpay):
    """Test payment status transitions"""
    payment_id = 'pay_test123'
    
    # Initial status
    success, status_data = payment_gateway.get_payment_status(payment_id)
    assert status_data['status'] == 'captured'
    
    # After refund
    payment_gateway.refund_payment(payment_id)
    success, status_data = payment_gateway.get_payment_status(payment_id)
    assert 'refund' in status_data['status'].lower()

def test_concurrent_refund_requests(payment_gateway, mock_razorpay):
    """Test handling concurrent refund requests"""
    payment_id = 'pay_test123'
    
    # First refund
    success1, refund1 = payment_gateway.refund_payment(payment_id)
    assert success1 == True
    
    # Second refund (should fail)
    success2, refund2 = payment_gateway.refund_payment(payment_id)
    assert success2 == False
    assert 'error' in refund2