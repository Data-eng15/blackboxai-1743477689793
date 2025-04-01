from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas
from typing import Dict, List
import os
from datetime import datetime
import json

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.report_folder = "reports"
        
        # Create reports directory if it doesn't exist
        if not os.path.exists(self.report_folder):
            os.makedirs(self.report_folder)

    def generate_report(self, application_data: Dict, assessment_data: Dict) -> str:
        """
        Generate a detailed PDF report for the loan assessment
        Returns the path to the generated PDF file
        """
        # Create filename
        filename = f"loan_report_{application_data['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.report_folder, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build content
        story = []
        
        # Add header
        self._add_header(story)
        
        # Add applicant details
        self._add_applicant_details(story, application_data)
        
        # Add assessment summary
        self._add_assessment_summary(story, assessment_data)
        
        # Add detailed analysis
        self._add_detailed_analysis(story, assessment_data)
        
        # Add recommendations
        self._add_recommendations(story, assessment_data)
        
        # Add disclaimer
        self._add_disclaimer(story)
        
        # Build PDF
        doc.build(story)
        
        return filepath

    def _add_header(self, story: List):
        """Add report header"""
        header_style = ParagraphStyle(
            'Header',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        story.append(Paragraph("Loan Assessment Report", header_style))
        story.append(Paragraph(
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 20))

    def _add_applicant_details(self, story: List, application_data: Dict):
        """Add applicant details section"""
        story.append(Paragraph("Applicant Details", self.styles['Heading2']))
        
        data = [
            ["Full Name", application_data.get('full_name', '')],
            ["Date of Birth", application_data.get('date_of_birth', '')],
            ["Employment", application_data.get('employment_type', '')],
            ["Monthly Income", f"₹{application_data.get('monthly_income', 0):,.2f}"],
            ["Loan Amount Requested", f"₹{application_data.get('loan_amount', 0):,.2f}"],
            ["Loan Purpose", application_data.get('loan_purpose', '')],
            ["Loan Tenure", f"{application_data.get('loan_tenure', 0)} months"]
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))

    def _add_assessment_summary(self, story: List, assessment_data: Dict):
        """Add assessment summary section"""
        story.append(Paragraph("Assessment Summary", self.styles['Heading2']))
        
        # Create summary table
        data = [
            ["Credit Score", str(assessment_data.get('credit_score', ''))],
            ["Approved Amount", f"₹{assessment_data.get('approved_amount', 0):,.2f}"],
            ["Interest Rate", f"{assessment_data.get('interest_rate', 0)}%"],
            ["Risk Assessment", assessment_data.get('risk_assessment', '').title()],
            ["Monthly EMI", f"₹{assessment_data.get('monthly_emi', 0):,.2f}"],
            ["Total Interest", f"₹{assessment_data.get('total_interest', 0):,.2f}"]
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))

    def _add_detailed_analysis(self, story: List, assessment_data: Dict):
        """Add detailed analysis section"""
        story.append(Paragraph("Detailed Analysis", self.styles['Heading2']))
        
        # Add factors considered
        story.append(Paragraph("Factors Considered:", self.styles['Heading3']))
        for factor in assessment_data.get('factors_considered', []):
            story.append(Paragraph(f"• {factor}", self.styles['Normal']))
        
        story.append(Spacer(1, 10))
        
        # Add eligibility metrics
        story.append(Paragraph("Eligibility Metrics:", self.styles['Heading3']))
        eligibility = assessment_data.get('eligibility_summary', {})
        
        data = [
            ["Income Multiplier", f"{eligibility.get('income_multiplier', 0):.2f}x"],
            ["EMI to Income Ratio", f"{eligibility.get('emi_to_income_ratio', 0)*100:.1f}%"],
            ["Approval Percentage", f"{eligibility.get('approval_percentage', 0):.1f}%"]
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))

    def _add_recommendations(self, story: List, assessment_data: Dict):
        """Add recommendations section"""
        story.append(Paragraph("Recommendations", self.styles['Heading2']))
        
        for recommendation in assessment_data.get('recommendations', []):
            story.append(Paragraph(f"• {recommendation}", self.styles['Normal']))
        
        story.append(Spacer(1, 20))

    def _add_disclaimer(self, story: List):
        """Add disclaimer section"""
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey
        )
        
        disclaimer_text = """
        Disclaimer: This report is generated based on the information provided and our AI-powered assessment system. 
        The approved loan amount, interest rate, and other terms are tentative and subject to final verification by the lending partners. 
        The actual loan offer may vary based on additional factors and the lending partner's policies. 
        This report is valid for 30 days from the date of generation.
        """
        
        story.append(Paragraph("Disclaimer", self.styles['Heading3']))
        story.append(Paragraph(disclaimer_text, disclaimer_style))