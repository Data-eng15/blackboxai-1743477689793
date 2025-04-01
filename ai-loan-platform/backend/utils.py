import re
from datetime import datetime, date
import json
from typing import Dict, Any, Union, List
import os
import magic
from werkzeug.utils import secure_filename
from .error_handlers import ValidationError

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    pattern = r'^\+?[1-9]\d{9,14}$'
    return bool(re.match(pattern, phone))

def validate_aadhaar(aadhaar: str) -> bool:
    """Validate Aadhaar number format"""
    pattern = r'^\d{12}$'
    return bool(re.match(pattern, aadhaar))

def validate_pan(pan: str) -> bool:
    """Validate PAN number format"""
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
    return bool(re.match(pattern, pan))

def validate_pincode(pincode: str) -> bool:
    """Validate pincode format"""
    pattern = r'^\d{6}$'
    return bool(re.match(pattern, pincode))

def calculate_age(dob: date) -> int:
    """Calculate age from date of birth"""
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def format_currency(amount: float) -> str:
    """Format amount as Indian currency"""
    return f"₹{amount:,.2f}"

def calculate_emi(principal: float, rate: float, tenure: int) -> float:
    """Calculate EMI for loan
    Args:
        principal: Loan amount
        rate: Annual interest rate (in percentage)
        tenure: Loan tenure in months
    """
    monthly_rate = rate / (12 * 100)
    emi = (principal * monthly_rate * (1 + monthly_rate)**tenure) / ((1 + monthly_rate)**tenure - 1)
    return round(emi, 2)

def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_mime_type(file_path: str) -> str:
    """Get MIME type of file"""
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path)

def save_uploaded_file(file, upload_folder: str, allowed_extensions: set) -> str:
    """Save uploaded file and return file path
    
    Args:
        file: FileStorage object
        upload_folder: Path to upload folder
        allowed_extensions: Set of allowed file extensions
    
    Returns:
        str: Path to saved file
    
    Raises:
        ValidationError: If file type is not allowed
    """
    if not allowed_file(file.filename, allowed_extensions):
        raise ValidationError('File type not allowed')
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)
    
    # Create directory if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)
    
    file.save(file_path)
    
    # Verify file type
    mime_type = get_file_mime_type(file_path)
    if not is_safe_mime_type(mime_type):
        os.remove(file_path)
        raise ValidationError('File type not allowed')
    
    return file_path

def is_safe_mime_type(mime_type: str) -> bool:
    """Check if MIME type is safe"""
    safe_mimes = {
        'application/pdf',
        'image/jpeg',
        'image/png',
        'image/jpg'
    }
    return mime_type in safe_mimes

def validate_loan_application(data: Dict[str, Any]) -> List[str]:
    """Validate loan application data
    
    Returns:
        List of validation error messages
    """
    errors = []
    
    # Required fields
    required_fields = [
        'full_name', 'date_of_birth', 'pan_number', 'aadhaar_number',
        'phone', 'address_line1', 'city', 'state', 'pincode',
        'employment_type', 'monthly_income', 'loan_amount', 'loan_tenure'
    ]
    
    for field in required_fields:
        if not data.get(field):
            errors.append(f'{field} is required')
    
    # Validate formats
    if data.get('email') and not validate_email(data['email']):
        errors.append('Invalid email format')
    
    if data.get('phone') and not validate_phone(data['phone']):
        errors.append('Invalid phone number format')
    
    if data.get('aadhaar_number') and not validate_aadhaar(data['aadhaar_number']):
        errors.append('Invalid Aadhaar number format')
    
    if data.get('pan_number') and not validate_pan(data['pan_number']):
        errors.append('Invalid PAN number format')
    
    if data.get('pincode') and not validate_pincode(data['pincode']):
        errors.append('Invalid pincode format')
    
    # Validate amounts
    if data.get('monthly_income'):
        try:
            income = float(data['monthly_income'])
            if income <= 0:
                errors.append('Monthly income must be greater than 0')
        except ValueError:
            errors.append('Invalid monthly income value')
    
    if data.get('loan_amount'):
        try:
            loan_amount = float(data['loan_amount'])
            if loan_amount <= 0:
                errors.append('Loan amount must be greater than 0')
        except ValueError:
            errors.append('Invalid loan amount value')
    
    # Validate age
    if data.get('date_of_birth'):
        try:
            dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            age = calculate_age(dob)
            if age < 18:
                errors.append('Applicant must be at least 18 years old')
            if age > 65:
                errors.append('Applicant must be under 65 years old')
        except ValueError:
            errors.append('Invalid date of birth format')
    
    return errors

def mask_aadhaar(aadhaar: str) -> str:
    """Mask Aadhaar number for display"""
    return 'XXXX-XXXX-' + aadhaar[-4:]

def mask_pan(pan: str) -> str:
    """Mask PAN number for display"""
    return pan[:2] + 'XXXX' + pan[-4:]

def format_date(date_obj: Union[date, datetime]) -> str:
    """Format date for display"""
    return date_obj.strftime('%d-%m-%Y')

def to_json_serializable(obj: Any) -> Any:
    """Convert object to JSON serializable format"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, (list, tuple)):
        return [to_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: to_json_serializable(value) for key, value in obj.items()}
    elif hasattr(obj, '__dict__'):
        return to_json_serializable(obj.__dict__)
    return obj