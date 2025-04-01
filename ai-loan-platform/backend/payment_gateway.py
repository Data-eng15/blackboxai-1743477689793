import razorpay
import os
from typing import Dict, Tuple
import hmac
import hashlib
import json
from datetime import datetime

class PaymentGateway:
    def __init__(self):
        self.client = razorpay.Client(
            auth=(
                os.getenv('RAZORPAY_KEY_ID'),
                os.getenv('RAZORPAY_KEY_SECRET')
            )
        )
        self.report_fee = 120  # ₹120 fixed fee for the report

    def create_order(self, user_id: int, application_id: int) -> Tuple[bool, Dict]:
        """
        Create a new payment order for the report fee
        """
        try:
            order_data = {
                'amount': self.report_fee * 100,  # Amount in paise
                'currency': 'INR',
                'receipt': f'REPORT-{application_id}',
                'notes': {
                    'user_id': str(user_id),
                    'application_id': str(application_id),
                    'purpose': 'loan_assessment_report'
                }
            }
            
            order = self.client.order.create(data=order_data)
            
            return True, {
                'order_id': order['id'],
                'amount': order['amount'] / 100,  # Convert back to rupees
                'currency': order['currency'],
                'receipt': order['receipt']
            }
            
        except Exception as e:
            return False, {'error': str(e)}

    def verify_payment(self, payment_data: Dict) -> Tuple[bool, Dict]:
        """
        Verify payment signature and update payment status
        """
        try:
            # Extract payment details
            razorpay_order_id = payment_data.get('razorpay_order_id')
            razorpay_payment_id = payment_data.get('razorpay_payment_id')
            razorpay_signature = payment_data.get('razorpay_signature')
            
            # Verify signature
            if not self._verify_signature(
                razorpay_order_id,
                razorpay_payment_id,
                razorpay_signature
            ):
                return False, {'error': 'Invalid payment signature'}
            
            # Fetch payment details from Razorpay
            payment = self.client.payment.fetch(razorpay_payment_id)
            
            if payment['status'] != 'captured':
                return False, {'error': 'Payment not captured'}
            
            # Extract application details from order notes
            application_id = payment.get('notes', {}).get('application_id')
            
            return True, {
                'payment_id': razorpay_payment_id,
                'order_id': razorpay_order_id,
                'amount': payment['amount'] / 100,
                'status': payment['status'],
                'application_id': application_id,
                'payment_method': payment.get('method'),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return False, {'error': str(e)}

    def _verify_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        """
        Verify Razorpay payment signature
        """
        key_secret = os.getenv('RAZORPAY_KEY_SECRET')
        msg = f'{order_id}|{payment_id}'
        
        generated_signature = hmac.new(
            key_secret.encode(),
            msg.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(generated_signature, signature)

    def refund_payment(self, payment_id: str, amount: int = None) -> Tuple[bool, Dict]:
        """
        Process refund for a payment
        """
        try:
            refund_data = {'payment_id': payment_id}
            if amount:
                refund_data['amount'] = amount * 100  # Convert to paise
            
            refund = self.client.payment.refund(payment_id, refund_data)
            
            return True, {
                'refund_id': refund['id'],
                'payment_id': refund['payment_id'],
                'amount': refund['amount'] / 100,
                'status': refund['status'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return False, {'error': str(e)}

    def get_payment_status(self, payment_id: str) -> Tuple[bool, Dict]:
        """
        Get current status of a payment
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            
            return True, {
                'payment_id': payment['id'],
                'order_id': payment['order_id'],
                'amount': payment['amount'] / 100,
                'status': payment['status'],
                'method': payment.get('method'),
                'timestamp': datetime.fromtimestamp(payment['created_at']).isoformat()
            }
            
        except Exception as e:
            return False, {'error': str(e)}

    def generate_payment_receipt(self, payment_data: Dict) -> Dict:
        """
        Generate payment receipt data
        """
        return {
            'receipt_number': f"RCP-{payment_data['payment_id'][-8:]}",
            'date': datetime.now().strftime('%Y-%m-%d'),
            'amount': payment_data['amount'],
            'payment_id': payment_data['payment_id'],
            'order_id': payment_data['order_id'],
            'payment_method': payment_data.get('payment_method', 'Online'),
            'description': 'Loan Assessment Report Fee',
            'status': 'Paid',
            'customer_details': {
                'application_id': payment_data.get('application_id')
            }
        }