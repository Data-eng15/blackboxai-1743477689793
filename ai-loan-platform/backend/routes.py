from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from .models import db, User, LoanApplication, UserDocument, Payment, AuditLog
from .loan_assessment import LoanAssessment
from .document_verification import DocumentVerification
from .payment_gateway import PaymentGateway
from .report_generator import ReportGenerator

# Initialize blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
loan_bp = Blueprint('loan', __name__, url_prefix='/api/loan')
document_bp = Blueprint('document', __name__, url_prefix='/api/document')
payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

# Initialize services
loan_assessor = LoanAssessment()
doc_verifier = DocumentVerification()
payment_gateway = PaymentGateway()
report_generator = ReportGenerator()

# Authentication routes
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    user = User(
        email=data['email'],
        name=data.get('name'),
        phone=data.get('phone')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token}), 200

# Loan application routes
@loan_bp.route('/apply', methods=['POST'])
@jwt_required()
def submit_application():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    application = LoanApplication(
        user_id=user_id,
        status='submitted',
        submitted_at=datetime.utcnow(),
        **data
    )
    
    db.session.add(application)
    db.session.commit()
    
    # Log the action
    log = AuditLog(
        user_id=user_id,
        application_id=application.id,
        action='application_submitted',
        details={'application_data': data},
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': 'Application submitted successfully',
        'application_id': application.id
    }), 201

@loan_bp.route('/application/<int:application_id>', methods=['GET'])
@jwt_required()
def get_application(application_id):
    user_id = get_jwt_identity()
    application = LoanApplication.query.filter_by(
        id=application_id,
        user_id=user_id
    ).first_or_404()
    
    return jsonify({
        'id': application.id,
        'status': application.status,
        'approved_amount': application.approved_amount,
        'interest_rate': application.interest_rate,
        'monthly_emi': application.monthly_emi,
        'documents_verified': {
            'aadhaar': application.aadhaar_verified,
            'pan': application.pan_verified,
            'income': application.income_verified,
            'address': application.address_verified
        }
    }), 200

# Document verification routes
@document_bp.route('/digilocker/auth', methods=['GET'])
@jwt_required()
def get_digilocker_auth_url():
    auth_url = doc_verifier.generate_digilocker_auth_url()
    return jsonify({'auth_url': auth_url}), 200

@document_bp.route('/digilocker/callback', methods=['GET'])
@jwt_required()
def handle_digilocker_callback():
    user_id = get_jwt_identity()
    auth_code = request.args.get('code')
    
    success, documents = doc_verifier.handle_digilocker_callback(auth_code)
    
    if not success:
        return jsonify({'error': 'Failed to fetch documents'}), 400
    
    # Store fetched documents
    for doc_type, doc_data in documents.items():
        document = UserDocument(
            user_id=user_id,
            document_type=doc_type,
            verification_method='digilocker',
            verification_details=doc_data,
            is_verified=True,
            verified_at=datetime.utcnow()
        )
        db.session.add(document)
    
    db.session.commit()
    
    return jsonify({'message': 'Documents fetched successfully'}), 200

@document_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    doc_type = request.form.get('document_type')
    
    if not file or not file.filename:
        return jsonify({'error': 'No file selected'}), 400
    
    if not doc_type:
        return jsonify({'error': 'Document type not specified'}), 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    # Save file
    file.save(file_path)
    
    # Create document record
    document = UserDocument(
        user_id=user_id,
        document_type=doc_type,
        file_path=file_path,
        file_name=filename,
        file_size=os.path.getsize(file_path),
        mime_type=file.content_type,
        verification_method='manual_upload'
    )
    
    db.session.add(document)
    db.session.commit()
    
    return jsonify({
        'message': 'Document uploaded successfully',
        'document_id': document.id
    }), 201

# Payment routes
@payment_bp.route('/create-order', methods=['POST'])
@jwt_required()
def create_payment_order():
    user_id = get_jwt_identity()
    application_id = request.json.get('application_id')
    
    success, order_data = payment_gateway.create_order(user_id, application_id)
    
    if not success:
        return jsonify({'error': 'Failed to create payment order'}), 400
    
    return jsonify(order_data), 200

@payment_bp.route('/verify', methods=['POST'])
@jwt_required()
def verify_payment():
    user_id = get_jwt_identity()
    payment_data = request.json
    
    success, verification_data = payment_gateway.verify_payment(payment_data)
    
    if not success:
        return jsonify({'error': 'Payment verification failed'}), 400
    
    # Update application payment status
    application = LoanApplication.query.get(verification_data['application_id'])
    application.payment_status = 'completed'
    application.payment_id = verification_data['payment_id']
    application.payment_amount = verification_data['amount']
    application.payment_date = datetime.utcnow()
    
    # Generate report
    report_path = report_generator.generate_report(
        application_data=application.__dict__,
        assessment_data=loan_assessor.generate_report_data(application.__dict__)
    )
    
    application.report_generated = True
    application.report_path = report_path
    
    db.session.commit()
    
    return jsonify({
        'message': 'Payment verified and report generated',
        'payment_id': verification_data['payment_id']
    }), 200

def init_app(app):
    """Initialize routes with the Flask app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(loan_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(payment_bp)