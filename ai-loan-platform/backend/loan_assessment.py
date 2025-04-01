from typing import Dict, Tuple, List
import math

class LoanAssessment:
    def __init__(self):
        # Risk weights for different factors
        self.weights = {
            'income': 0.35,
            'employment': 0.25,
            'education': 0.15,
            'loan_amount_ratio': 0.15,
            'work_experience': 0.10
        }
        
        # Employment type scores
        self.employment_scores = {
            'full_time': 100,
            'part_time': 70,
            'self_employed': 80,
            'business_owner': 85,
            'contract': 75,
            'freelance': 65
        }
        
        # Education level scores
        self.education_scores = {
            'post_graduate': 100,
            'graduate': 90,
            'under_graduate': 80,
            'diploma': 75,
            'high_school': 70
        }

    def calculate_credit_score(self, application_data: Dict) -> int:
        """
        Calculate credit score based on application data
        Returns a score between 300 and 900
        """
        score = 0
        
        # Income score (0-100)
        monthly_income = float(application_data.get('monthly_income', 0))
        income_score = min(100, (monthly_income / 100000) * 100)
        score += income_score * self.weights['income']
        
        # Employment score (0-100)
        employment_type = application_data.get('employment_type', 'full_time').lower()
        employment_score = self.employment_scores.get(employment_type, 60)
        score += employment_score * self.weights['employment']
        
        # Education score (0-100)
        education_level = application_data.get('education_level', 'graduate').lower()
        education_score = self.education_scores.get(education_level, 70)
        score += education_score * self.weights['education']
        
        # Loan amount to income ratio score (0-100)
        loan_amount = float(application_data.get('loan_amount', 0))
        loan_ratio = (loan_amount / (monthly_income * 12))
        loan_ratio_score = max(0, 100 - (loan_ratio * 100))
        score += loan_ratio_score * self.weights['loan_amount_ratio']
        
        # Work experience score (0-100)
        experience = int(application_data.get('work_experience', 0))
        experience_score = min(100, (experience / 10) * 100)
        score += experience_score * self.weights['work_experience']
        
        # Convert to credit score range (300-900)
        credit_score = 300 + int((score / 100) * 600)
        return credit_score

    def assess_loan_eligibility(self, application_data: Dict) -> Tuple[float, float, str, List[str]]:
        """
        Assess loan eligibility and return:
        - approved_amount
        - interest_rate
        - risk_assessment
        - factors_considered
        """
        credit_score = self.calculate_credit_score(application_data)
        monthly_income = float(application_data.get('monthly_income', 0))
        loan_amount = float(application_data.get('loan_amount', 0))
        
        # Calculate maximum eligible loan amount (up to 36 times monthly income)
        max_eligible_amount = monthly_income * 36
        
        # Determine approval amount based on credit score
        if credit_score >= 750:
            approved_ratio = 1.0  # 100% of requested amount
        elif credit_score >= 650:
            approved_ratio = 0.8  # 80% of requested amount
        elif credit_score >= 550:
            approved_ratio = 0.6  # 60% of requested amount
        else:
            approved_ratio = 0.0  # Not eligible
        
        approved_amount = min(loan_amount * approved_ratio, max_eligible_amount)
        
        # Calculate interest rate based on credit score
        if credit_score >= 800:
            interest_rate = 10.0
        elif credit_score >= 750:
            interest_rate = 12.0
        elif credit_score >= 700:
            interest_rate = 14.0
        elif credit_score >= 650:
            interest_rate = 16.0
        elif credit_score >= 600:
            interest_rate = 18.0
        else:
            interest_rate = 20.0
        
        # Determine risk assessment
        if credit_score >= 750:
            risk_assessment = 'low'
        elif credit_score >= 650:
            risk_assessment = 'moderate'
        elif credit_score >= 550:
            risk_assessment = 'high'
        else:
            risk_assessment = 'very_high'
        
        # Compile factors considered
        factors = [
            f"Credit Score: {credit_score}",
            f"Monthly Income: ₹{monthly_income:,.2f}",
            f"Loan Amount Requested: ₹{loan_amount:,.2f}",
            f"Employment Type: {application_data.get('employment_type', 'Not Specified')}",
            f"Work Experience: {application_data.get('work_experience', 0)} years",
            f"Education Level: {application_data.get('education_level', 'Not Specified')}"
        ]
        
        return approved_amount, interest_rate, risk_assessment, factors

    def generate_report_data(self, application_data: Dict) -> Dict:
        """
        Generate comprehensive loan assessment report data
        """
        credit_score = self.calculate_credit_score(application_data)
        approved_amount, interest_rate, risk_assessment, factors = self.assess_loan_eligibility(application_data)
        
        monthly_income = float(application_data.get('monthly_income', 0))
        loan_amount = float(application_data.get('loan_amount', 0))
        loan_tenure = int(application_data.get('loan_tenure', 12))
        
        # Calculate EMI
        if approved_amount > 0:
            monthly_interest = (interest_rate / 100) / 12
            emi = (approved_amount * monthly_interest * math.pow(1 + monthly_interest, loan_tenure)) / (math.pow(1 + monthly_interest, loan_tenure) - 1)
        else:
            emi = 0
        
        report_data = {
            'credit_score': credit_score,
            'approved_amount': approved_amount,
            'interest_rate': interest_rate,
            'risk_assessment': risk_assessment,
            'factors_considered': factors,
            'monthly_emi': emi,
            'loan_tenure': loan_tenure,
            'total_interest': (emi * loan_tenure) - approved_amount if approved_amount > 0 else 0,
            'debt_to_income_ratio': (emi / monthly_income) if monthly_income > 0 else 0,
            'eligibility_summary': {
                'income_multiplier': approved_amount / monthly_income if monthly_income > 0 else 0,
                'emi_to_income_ratio': (emi / monthly_income) if monthly_income > 0 else 0,
                'approval_percentage': (approved_amount / loan_amount * 100) if loan_amount > 0 else 0
            },
            'recommendations': self._generate_recommendations(credit_score, approved_amount, loan_amount, emi, monthly_income)
        }
        
        return report_data

    def _generate_recommendations(self, credit_score: int, approved_amount: float, 
                                loan_amount: float, emi: float, monthly_income: float) -> List[str]:
        """
        Generate personalized recommendations based on assessment results
        """
        recommendations = []
        
        if credit_score < 750:
            recommendations.append("Consider improving your credit score to get better loan terms.")
            
        if approved_amount < loan_amount:
            recommendations.append("The approved loan amount is less than requested. Consider reducing the loan amount or improving your eligibility factors.")
            
        if emi > (monthly_income * 0.5):
            recommendations.append("The EMI is high compared to your income. Consider a longer tenure or lower loan amount.")
            
        if credit_score < 650:
            recommendations.append("Adding a co-applicant with good credit history might improve loan eligibility.")
            
        if monthly_income < 50000:
            recommendations.append("Consider ways to increase your income to improve loan eligibility.")
        
        return recommendations