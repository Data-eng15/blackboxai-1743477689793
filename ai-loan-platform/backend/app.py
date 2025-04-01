from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import timedelta

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///loan_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-here')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    applications = db.relationship('LoanApplication', backref='user', lazy=True)

class LoanApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    # Personal Details
    full_name = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    pan_number = db.Column(db.String(10))
    aadhaar_number = db.Column(db.String(12))
    # Address
    address_line1 = db.Column(db.String(255))
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(6))
    # Education & Employment
    education_level = db.Column(db.String(50))
    employment_type = db.Column(db.String(50))
    employer_name = db.Column(db.String(100))
    monthly_income = db.Column(db.Float)
    work_experience = db.Column(db.Integer)  # in years
    # Loan Details
    loan_amount = db.Column(db.Float)
    loan_purpose = db.Column(db.String(255))
    loan_tenure = db.Column(db.Integer)  # in months
    # Document Verification
    aadhaar_verified = db.Column(db.Boolean, default=False)
    pan_verified = db.Column(db.Boolean, default=False)
    bank_statements = db.Column(db.String(255))  # file path
    salary_slips = db.Column(db.String(255))  # file path
    # AI Analysis Results
    credit_score = db.Column(db.Integer)
    approved_amount = db.Column(db.Float)
    interest_rate = db.Column(db.Float)
    risk_assessment = db.Column(db.String(50))
    # Payment Status
    payment_status = db.Column(db.String(50), default='pending')
    payment_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

# Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    user = User(
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        name=data.get('name'),
        phone=data.get('phone')
    )
    
    db.session.add(user)
    db.session.commit()
    
    access_token = create_access_token(identity=user.id)
    return jsonify({
        'message': 'User registered successfully',
        'access_token': access_token
    }), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token
    }), 200

@app.route('/api/apply', methods=['POST'])
@jwt_required()
def submit_application():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Create new loan application
    application = LoanApplication(
        user_id=user_id,
        full_name=data.get('full_name'),
        date_of_birth=data.get('date_of_birth'),
        pan_number=data.get('pan_number'),
        aadhaar_number=data.get('aadhaar_number'),
        address_line1=data.get('address_line1'),
        address_line2=data.get('address_line2'),
        city=data.get('city'),
        state=data.get('state'),
        pincode=data.get('pincode'),
        education_level=data.get('education_level'),
        employment_type=data.get('employment_type'),
        employer_name=data.get('employer_name'),
        monthly_income=data.get('monthly_income'),
        work_experience=data.get('work_experience'),
        loan_amount=data.get('loan_amount'),
        loan_purpose=data.get('loan_purpose'),
        loan_tenure=data.get('loan_tenure')
    )
    
    db.session.add(application)
    db.session.commit()
    
    return jsonify({
        'message': 'Application submitted successfully',
        'application_id': application.id
    }), 201

@app.route('/api/application/<int:application_id>', methods=['GET'])
@jwt_required()
def get_application(application_id):
    user_id = get_jwt_identity()
    application = LoanApplication.query.filter_by(id=application_id, user_id=user_id).first()
    
    if not application:
        return jsonify({'error': 'Application not found'}), 404
    
    return jsonify({
        'id': application.id,
        'status': application.status,
        'approved_amount': application.approved_amount,
        'interest_rate': application.interest_rate,
        'risk_assessment': application.risk_assessment,
        'payment_status': application.payment_status
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)