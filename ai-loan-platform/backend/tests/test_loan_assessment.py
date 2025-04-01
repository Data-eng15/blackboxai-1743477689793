import pytest
from backend.loan_assessment import LoanAssessment

@pytest.fixture
def loan_assessor():
    """Provide a loan assessment instance"""
    return LoanAssessment()

@pytest.fixture
def sample_application_data():
    """Provide sample application data"""
    return {
        'monthly_income': 50000,
        'employment_type': 'full_time',
        'education_level': 'graduate',
        'work_experience': 5,
        'loan_amount': 500000,
        'loan_tenure': 24
    }

def test_credit_score_calculation(loan_assessor, sample_application_data):
    """Test credit score calculation"""
    credit_score = loan_assessor.calculate_credit_score(sample_application_data)
    
    # Credit score should be between 300 and 900
    assert 300 <= credit_score <= 900
    
    # Test with different income levels
    high_income_data = sample_application_data.copy()
    high_income_data['monthly_income'] = 200000
    high_income_score = loan_assessor.calculate_credit_score(high_income_data)
    
    low_income_data = sample_application_data.copy()
    low_income_data['monthly_income'] = 20000
    low_income_score = loan_assessor.calculate_credit_score(low_income_data)
    
    # Higher income should result in higher score
    assert high_income_score > low_income_score

def test_loan_eligibility_assessment(loan_assessor, sample_application_data):
    """Test loan eligibility assessment"""
    approved_amount, interest_rate, risk_assessment, factors = \
        loan_assessor.assess_loan_eligibility(sample_application_data)
    
    # Check approved amount
    assert approved_amount >= 0
    assert approved_amount <= sample_application_data['loan_amount']
    
    # Check interest rate
    assert 8 <= interest_rate <= 24
    
    # Check risk assessment
    assert risk_assessment in ['low', 'moderate', 'high', 'very_high']
    
    # Check factors considered
    assert len(factors) > 0
    assert all(isinstance(factor, str) for factor in factors)

def test_employment_type_impact(loan_assessor):
    """Test impact of different employment types"""
    base_data = {
        'monthly_income': 50000,
        'education_level': 'graduate',
        'work_experience': 5,
        'loan_amount': 500000,
        'loan_tenure': 24
    }
    
    employment_scores = {}
    for emp_type in ['full_time', 'part_time', 'self_employed', 'business_owner']:
        data = base_data.copy()
        data['employment_type'] = emp_type
        score = loan_assessor.calculate_credit_score(data)
        employment_scores[emp_type] = score
    
    # Full-time should have highest score
    assert employment_scores['full_time'] >= employment_scores['part_time']
    assert employment_scores['full_time'] >= employment_scores['self_employed']

def test_education_level_impact(loan_assessor):
    """Test impact of different education levels"""
    base_data = {
        'monthly_income': 50000,
        'employment_type': 'full_time',
        'work_experience': 5,
        'loan_amount': 500000,
        'loan_tenure': 24
    }
    
    education_scores = {}
    for edu_level in ['post_graduate', 'graduate', 'under_graduate']:
        data = base_data.copy()
        data['education_level'] = edu_level
        score = loan_assessor.calculate_credit_score(data)
        education_scores[edu_level] = score
    
    # Higher education should result in higher score
    assert education_scores['post_graduate'] >= education_scores['graduate']
    assert education_scores['graduate'] >= education_scores['under_graduate']

def test_loan_amount_ratio_impact(loan_assessor):
    """Test impact of loan amount to income ratio"""
    base_data = {
        'monthly_income': 50000,
        'employment_type': 'full_time',
        'education_level': 'graduate',
        'work_experience': 5,
        'loan_tenure': 24
    }
    
    # Test with different loan amounts
    conservative_data = base_data.copy()
    conservative_data['loan_amount'] = 300000  # 6x monthly income
    
    aggressive_data = base_data.copy()
    aggressive_data['loan_amount'] = 1000000  # 20x monthly income
    
    conservative_score = loan_assessor.calculate_credit_score(conservative_data)
    aggressive_score = loan_assessor.calculate_credit_score(aggressive_data)
    
    # Lower loan amount ratio should result in higher score
    assert conservative_score > aggressive_score

def test_report_data_generation(loan_assessor, sample_application_data):
    """Test comprehensive report data generation"""
    report_data = loan_assessor.generate_report_data(sample_application_data)
    
    # Check required fields
    assert 'credit_score' in report_data
    assert 'approved_amount' in report_data
    assert 'interest_rate' in report_data
    assert 'risk_assessment' in report_data
    assert 'factors_considered' in report_data
    assert 'monthly_emi' in report_data
    assert 'eligibility_summary' in report_data
    assert 'recommendations' in report_data
    
    # Check EMI calculation
    if report_data['approved_amount'] > 0:
        assert report_data['monthly_emi'] > 0
        total_repayment = report_data['monthly_emi'] * sample_application_data['loan_tenure']
        assert total_repayment > report_data['approved_amount']  # Due to interest
    
    # Check recommendations
    assert isinstance(report_data['recommendations'], list)
    assert len(report_data['recommendations']) > 0

def test_edge_cases(loan_assessor):
    """Test edge cases in loan assessment"""
    # Test with very high income
    high_income_data = {
        'monthly_income': 1000000,
        'employment_type': 'full_time',
        'education_level': 'post_graduate',
        'work_experience': 15,
        'loan_amount': 5000000,
        'loan_tenure': 24
    }
    
    # Test with very low income
    low_income_data = {
        'monthly_income': 10000,
        'employment_type': 'part_time',
        'education_level': 'high_school',
        'work_experience': 1,
        'loan_amount': 500000,
        'loan_tenure': 24
    }
    
    high_income_result = loan_assessor.assess_loan_eligibility(high_income_data)
    low_income_result = loan_assessor.assess_loan_eligibility(low_income_data)
    
    # High income should get better terms
    assert high_income_result[0] > low_income_result[0]  # Approved amount
    assert high_income_result[1] < low_income_result[1]  # Interest rate
    assert high_income_result[2] == 'low'  # Risk assessment