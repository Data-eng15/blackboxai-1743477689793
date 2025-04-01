import pytest
from backend.report_generator import ReportGenerator
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader

@pytest.fixture
def report_generator():
    """Provide a report generator instance"""
    return ReportGenerator()

@pytest.fixture
def sample_application_data():
    """Provide sample application data"""
    return {
        'id': 1,
        'full_name': 'Test User',
        'date_of_birth': '1990-01-01',
        'pan_number': 'ABCDE1234F',
        'aadhaar_number': '123456789012',
        'employment_type': 'full_time',
        'employer_name': 'Test Company',
        'monthly_income': 50000,
        'work_experience': 5,
        'loan_amount': 500000,
        'loan_purpose': 'personal',
        'loan_tenure': 24
    }

@pytest.fixture
def sample_assessment_data():
    """Provide sample assessment data"""
    return {
        'credit_score': 750,
        'approved_amount': 450000,
        'interest_rate': 12.5,
        'risk_assessment': 'low',
        'monthly_emi': 21500,
        'total_interest': 66000,
        'factors_considered': [
            'Credit Score: 750',
            'Monthly Income: ₹50,000',
            'Employment Type: Full Time',
            'Work Experience: 5 years'
        ],
        'eligibility_summary': {
            'income_multiplier': 9,
            'emi_to_income_ratio': 0.43,
            'approval_percentage': 90
        },
        'recommendations': [
            'Consider increasing loan tenure to reduce EMI burden',
            'Maintain good credit score for better interest rates'
        ]
    }

def test_report_generation(report_generator, sample_application_data, sample_assessment_data):
    """Test PDF report generation"""
    report_path = report_generator.generate_report(
        sample_application_data,
        sample_assessment_data
    )
    
    # Check if file was created
    assert os.path.exists(report_path)
    assert report_path.endswith('.pdf')
    
    # Verify PDF content
    pdf = PdfReader(report_path)
    text = ''
    for page in pdf.pages:
        text += page.extract_text()
    
    # Check for key sections
    assert 'Loan Assessment Report' in text
    assert sample_application_data['full_name'] in text
    assert str(sample_assessment_data['credit_score']) in text
    assert str(sample_assessment_data['approved_amount']) in text
    
    # Clean up
    os.remove(report_path)

def test_report_sections(report_generator, sample_application_data, sample_assessment_data):
    """Test individual report sections"""
    # Create a test story list
    story = []
    
    # Test header
    report_generator._add_header(story)
    assert len(story) > 0
    assert isinstance(story[-1].text, str)
    assert 'Generated on:' in story[-1].text
    
    # Test applicant details
    report_generator._add_applicant_details(story, sample_application_data)
    assert len(story) > 0
    
    # Test assessment summary
    report_generator._add_assessment_summary(story, sample_assessment_data)
    assert len(story) > 0
    
    # Test detailed analysis
    report_generator._add_detailed_analysis(story, sample_assessment_data)
    assert len(story) > 0
    
    # Test recommendations
    report_generator._add_recommendations(story, sample_assessment_data)
    assert len(story) > 0
    
    # Test disclaimer
    report_generator._add_disclaimer(story)
    assert len(story) > 0

def test_report_formatting(report_generator, sample_application_data, sample_assessment_data):
    """Test report formatting and styling"""
    report_path = report_generator.generate_report(
        sample_application_data,
        sample_assessment_data
    )
    
    # Check PDF metadata and formatting
    pdf = PdfReader(report_path)
    page = pdf.pages[0]
    
    # Check page size
    assert round(float(page.mediabox.width), 2) == round(float(A4[0]), 2)
    assert round(float(page.mediabox.height), 2) == round(float(A4[1]), 2)
    
    # Clean up
    os.remove(report_path)

def test_report_with_missing_data(report_generator):
    """Test report generation with missing data"""
    incomplete_application = {
        'id': 1,
        'full_name': 'Test User',
        'loan_amount': 500000
    }
    
    incomplete_assessment = {
        'credit_score': 750,
        'approved_amount': 450000
    }
    
    report_path = report_generator.generate_report(
        incomplete_application,
        incomplete_assessment
    )
    
    # Check if file was created despite missing data
    assert os.path.exists(report_path)
    
    # Clean up
    os.remove(report_path)

def test_report_file_naming(report_generator, sample_application_data, sample_assessment_data):
    """Test report file naming convention"""
    report_path = report_generator.generate_report(
        sample_application_data,
        sample_assessment_data
    )
    
    # Check filename format
    filename = os.path.basename(report_path)
    assert filename.startswith('loan_report_')
    assert filename.endswith('.pdf')
    assert str(sample_application_data['id']) in filename
    
    # Clean up
    os.remove(report_path)

def test_report_directory_creation(report_generator):
    """Test report directory creation"""
    # Remove reports directory if it exists
    if os.path.exists(report_generator.report_folder):
        os.rmdir(report_generator.report_folder)
    
    # Generate a report (should create directory)
    report_path = report_generator.generate_report(
        {'id': 1, 'full_name': 'Test'},
        {'credit_score': 750}
    )
    
    # Check if directory was created
    assert os.path.exists(report_generator.report_folder)
    assert os.path.isdir(report_generator.report_folder)
    
    # Clean up
    os.remove(report_path)
    os.rmdir(report_generator.report_folder)

def test_report_content_security(report_generator, sample_application_data, sample_assessment_data):
    """Test sensitive data handling in report"""
    report_path = report_generator.generate_report(
        sample_application_data,
        sample_assessment_data
    )
    
    # Read PDF content
    pdf = PdfReader(report_path)
    text = ''
    for page in pdf.pages:
        text += page.extract_text()
    
    # Check that sensitive data is masked
    assert sample_application_data['aadhaar_number'] not in text
    assert sample_application_data['pan_number'] not in text
    
    # Clean up
    os.remove(report_path)