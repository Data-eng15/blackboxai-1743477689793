import pytest
from datetime import datetime, date
from backend.models import User, LoanApplication, UserDocument, Payment, AuditLog
from werkzeug.security import check_password_hash

def test_user_model(session):
    """Test User model"""
    # Create user
    user = User(
        email='test@example.com',
        name='Test User',
        phone='+919876543210'
    )
    user.set_password('Test@123')
    
    session.add(user)
    session.commit()
    
    # Test retrieval
    saved_user = session.query(User).first()
    assert saved_user.email == 'test@example.com'
    assert saved_user.name == 'Test User'
    assert saved_user.phone == '+919876543210'
    
    # Test password hashing
    assert saved_user.password_hash != 'Test@123'
    assert check_password_hash(saved_user.password_hash, 'Test@123')
    
    # Test timestamps
    assert isinstance(saved_user.created_at, datetime)
    assert isinstance(saved_user.updated_at, datetime)

def test_loan_application_model(session):
    """Test LoanApplication model"""
    # Create user
    user = User(email='test@example.com')
    user.set_password('Test@123')
    session.add(user)
    session.commit()
    
    # Create loan application
    application = LoanApplication(
        user_id=user.id,
        full_name='Test User',
        date_of_birth=date(1990, 1, 1),
        pan_number='ABCDE1234F',
        aadhaar_number='123456789012',
        employment_type='full_time',
        employer_name='Test Company',
        monthly_income=50000,
        loan_amount=500000,
        loan_purpose='personal',
        loan_tenure=24
    )
    
    session.add(application)
    session.commit()
    
    # Test retrieval
    saved_application = session.query(LoanApplication).first()
    assert saved_application.full_name == 'Test User'
    assert saved_application.monthly_income == 50000
    assert saved_application.loan_amount == 500000
    
    # Test relationship with user
    assert saved_application.applicant.email == 'test@example.com'

def test_user_document_model(session):
    """Test UserDocument model"""
    # Create user
    user = User(email='test@example.com')
    user.set_password('Test@123')
    session.add(user)
    session.commit()
    
    # Create document
    document = UserDocument(
        user_id=user.id,
        document_type='aadhaar',
        file_path='/path/to/document.pdf',
        file_name='document.pdf',
        file_size=1024,
        mime_type='application/pdf',
        verification_method='digilocker'
    )
    
    session.add(document)
    session.commit()
    
    # Test retrieval
    saved_document = session.query(UserDocument).first()
    assert saved_document.document_type == 'aadhaar'
    assert saved_document.file_path == '/path/to/document.pdf'
    assert saved_document.is_verified == False
    
    # Test relationship with user
    assert saved_document.user.email == 'test@example.com'

def test_payment_model(session):
    """Test Payment model"""
    # Create user and application
    user = User(email='test@example.com')
    user.set_password('Test@123')
    session.add(user)
    session.commit()
    
    application = LoanApplication(user_id=user.id)
    session.add(application)
    session.commit()
    
    # Create payment
    payment = Payment(
        user_id=user.id,
        application_id=application.id,
        order_id='order_123',
        payment_id='pay_123',
        amount=120,
        status='captured',
        payment_method='card'
    )
    
    session.add(payment)
    session.commit()
    
    # Test retrieval
    saved_payment = session.query(Payment).first()
    assert saved_payment.order_id == 'order_123'
    assert saved_payment.amount == 120
    assert saved_payment.status == 'captured'

def test_audit_log_model(session):
    """Test AuditLog model"""
    # Create user and application
    user = User(email='test@example.com')
    user.set_password('Test@123')
    session.add(user)
    session.commit()
    
    application = LoanApplication(user_id=user.id)
    session.add(application)
    session.commit()
    
    # Create audit log
    log = AuditLog(
        user_id=user.id,
        application_id=application.id,
        action='application_submitted',
        details={'key': 'value'},
        ip_address='127.0.0.1',
        user_agent='Mozilla/5.0'
    )
    
    session.add(log)
    session.commit()
    
    # Test retrieval
    saved_log = session.query(AuditLog).first()
    assert saved_log.action == 'application_submitted'
    assert saved_log.details == {'key': 'value'}
    assert saved_log.ip_address == '127.0.0.1'

def test_user_relationships(session):
    """Test User model relationships"""
    # Create user
    user = User(email='test@example.com')
    user.set_password('Test@123')
    session.add(user)
    session.commit()
    
    # Add applications
    application1 = LoanApplication(user_id=user.id)
    application2 = LoanApplication(user_id=user.id)
    session.add_all([application1, application2])
    
    # Add documents
    document1 = UserDocument(
        user_id=user.id,
        document_type='aadhaar'
    )
    document2 = UserDocument(
        user_id=user.id,
        document_type='pan'
    )
    session.add_all([document1, document2])
    
    session.commit()
    
    # Test relationships
    saved_user = session.query(User).first()
    assert len(saved_user.applications) == 2
    assert len(saved_user.documents) == 2

def test_loan_application_status_transitions(session):
    """Test LoanApplication status transitions"""
    # Create user and application
    user = User(email='test@example.com')
    user.set_password('Test@123')
    session.add(user)
    session.commit()
    
    application = LoanApplication(
        user_id=user.id,
        status='draft'
    )
    session.add(application)
    session.commit()
    
    # Test status transitions
    application.status = 'submitted'
    session.commit()
    assert application.status == 'submitted'
    
    application.status = 'processing'
    session.commit()
    assert application.status == 'processing'
    
    application.status = 'approved'
    session.commit()
    assert application.status == 'approved'

def test_document_verification_status(session):
    """Test document verification status updates"""
    # Create user and document
    user = User(email='test@example.com')
    user.set_password('Test@123')
    session.add(user)
    session.commit()
    
    document = UserDocument(
        user_id=user.id,
        document_type='aadhaar',
        verification_method='digilocker'
    )
    session.add(document)
    session.commit()
    
    # Update verification status
    document.is_verified = True
    document.verified_at = datetime.utcnow()
    document.verification_details = {'method': 'digilocker', 'status': 'success'}
    session.commit()
    
    # Test updates
    saved_document = session.query(UserDocument).first()
    assert saved_document.is_verified == True
    assert isinstance(saved_document.verified_at, datetime)
    assert saved_document.verification_details['status'] == 'success'