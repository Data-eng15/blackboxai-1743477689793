from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and profile"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('LoanApplication', backref='applicant', lazy=True)
    documents = db.relationship('UserDocument', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class LoanApplication(db.Model):
    """Loan application model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='draft')  # draft, submitted, processing, approved, rejected
    
    # Personal Details
    full_name = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    pan_number = db.Column(db.String(10))
    aadhaar_number = db.Column(db.String(12))
    gender = db.Column(db.String(10))
    marital_status = db.Column(db.String(20))
    
    # Contact Details
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    alternate_phone = db.Column(db.String(20))
    
    # Address
    address_line1 = db.Column(db.String(255))
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(6))
    residence_type = db.Column(db.String(50))  # owned, rented, etc.
    years_at_residence = db.Column(db.Integer)
    
    # Education & Employment
    education_level = db.Column(db.String(50))
    employment_type = db.Column(db.String(50))
    employer_name = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    work_experience = db.Column(db.Integer)  # in years
    monthly_income = db.Column(db.Float)
    other_income = db.Column(db.Float)
    
    # Loan Details
    loan_amount = db.Column(db.Float)
    loan_purpose = db.Column(db.String(255))
    loan_tenure = db.Column(db.Integer)  # in months
    existing_loans = db.Column(db.Boolean, default=False)
    existing_emi = db.Column(db.Float, default=0)
    
    # Document Verification Status
    aadhaar_verified = db.Column(db.Boolean, default=False)
    pan_verified = db.Column(db.Boolean, default=False)
    income_verified = db.Column(db.Boolean, default=False)
    address_verified = db.Column(db.Boolean, default=False)
    
    # AI Assessment Results
    credit_score = db.Column(db.Integer)
    risk_assessment = db.Column(db.String(50))
    approved_amount = db.Column(db.Float)
    interest_rate = db.Column(db.Float)
    monthly_emi = db.Column(db.Float)
    approval_factors = db.Column(db.JSON)
    rejection_reasons = db.Column(db.JSON)
    
    # Payment Status
    payment_status = db.Column(db.String(50), default='pending')  # pending, completed, failed
    payment_id = db.Column(db.String(100))
    payment_amount = db.Column(db.Float)
    payment_date = db.Column(db.DateTime)
    
    # Report Details
    report_generated = db.Column(db.Boolean, default=False)
    report_path = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    processed_at = db.Column(db.DateTime)

class UserDocument(db.Model):
    """User document model for storing document details"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_type = db.Column(db.String(50))  # aadhaar, pan, bank_statement, salary_slip
    file_path = db.Column(db.String(255))
    file_name = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    is_verified = db.Column(db.Boolean, default=False)
    verification_method = db.Column(db.String(50))  # digilocker, manual_upload, ekyc
    verification_details = db.Column(db.JSON)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)

class Payment(db.Model):
    """Payment model for tracking report fee payments"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'), nullable=False)
    order_id = db.Column(db.String(100), unique=True)
    payment_id = db.Column(db.String(100), unique=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='INR')
    status = db.Column(db.String(50))  # created, authorized, captured, failed
    payment_method = db.Column(db.String(50))
    payment_details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(db.Model):
    """Audit log for tracking important actions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    application_id = db.Column(db.Integer, db.ForeignKey('loan_application.id'))
    action = db.Column(db.String(100))
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)