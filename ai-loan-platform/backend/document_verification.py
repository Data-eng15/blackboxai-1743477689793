import requests
from typing import Dict, Tuple, Optional
import os
from datetime import datetime
import hashlib
import base64
import json

class DocumentVerification:
    def __init__(self):
        # DigiLocker configuration
        self.digilocker_base_url = os.getenv('DIGILOCKER_BASE_URL', 'https://api.digitallocker.gov.in/public/oauth2/1/')
        self.digilocker_client_id = os.getenv('DIGILOCKER_CLIENT_ID')
        self.digilocker_client_secret = os.getenv('DIGILOCKER_CLIENT_SECRET')
        self.digilocker_redirect_uri = os.getenv('DIGILOCKER_REDIRECT_URI')

        # eKYC configuration
        self.ekyc_base_url = os.getenv('EKYC_BASE_URL')
        self.ekyc_api_key = os.getenv('EKYC_API_KEY')

    def generate_digilocker_auth_url(self) -> str:
        """
        Generate DigiLocker authorization URL for user consent
        """
        params = {
            'response_type': 'code',
            'client_id': self.digilocker_client_id,
            'redirect_uri': self.digilocker_redirect_uri,
            'state': self._generate_state_token(),
            'scope': 'aadhaar_pht pan_pht driving'
        }
        
        auth_url = f"{self.digilocker_base_url}/authorize?"
        auth_url += "&".join([f"{key}={value}" for key, value in params.items()])
        
        return auth_url

    def handle_digilocker_callback(self, auth_code: str) -> Tuple[bool, Dict]:
        """
        Handle DigiLocker callback and fetch user documents
        """
        try:
            # Exchange auth code for access token
            token_data = self._get_digilocker_token(auth_code)
            if not token_data.get('access_token'):
                return False, {'error': 'Failed to get access token'}

            access_token = token_data['access_token']
            
            # Fetch documents
            documents = {}
            
            # Fetch Aadhaar
            aadhaar_data = self._fetch_aadhaar(access_token)
            if aadhaar_data:
                documents['aadhaar'] = aadhaar_data
            
            # Fetch PAN
            pan_data = self._fetch_pan(access_token)
            if pan_data:
                documents['pan'] = pan_data
            
            return True, documents
            
        except Exception as e:
            return False, {'error': str(e)}

    def initiate_ekyc(self, aadhaar_number: str) -> Tuple[bool, Dict]:
        """
        Initiate eKYC process with Aadhaar number
        """
        try:
            # Hash Aadhaar number for security
            hashed_aadhaar = self._hash_aadhaar(aadhaar_number)
            
            # Make API call to initiate eKYC
            headers = {
                'Authorization': f'Bearer {self.ekyc_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'aadhaar_number': hashed_aadhaar,
                'consent': True,
                'consent_timestamp': datetime.utcnow().isoformat()
            }
            
            response = requests.post(
                f"{self.ekyc_base_url}/initiate",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return True, {
                    'request_id': data.get('request_id'),
                    'otp_sent': True
                }
            else:
                return False, {'error': 'Failed to initiate eKYC'}
            
        except Exception as e:
            return False, {'error': str(e)}

    def verify_ekyc_otp(self, request_id: str, otp: str) -> Tuple[bool, Dict]:
        """
        Verify OTP and complete eKYC process
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.ekyc_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'request_id': request_id,
                'otp': otp
            }
            
            response = requests.post(
                f"{self.ekyc_base_url}/verify-otp",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return True, self._process_ekyc_data(data)
            else:
                return False, {'error': 'OTP verification failed'}
            
        except Exception as e:
            return False, {'error': str(e)}

    def verify_bank_statement(self, file_path: str) -> Tuple[bool, Dict]:
        """
        Verify and analyze bank statement
        """
        try:
            # Implement bank statement analysis logic here
            # This could include:
            # - Verifying file authenticity
            # - Extracting transaction data
            # - Analyzing income patterns
            # - Checking for bounced checks
            # For now, return a mock analysis
            
            return True, {
                'verified': True,
                'average_balance': 50000,
                'monthly_credits': 75000,
                'salary_credits_found': True,
                'regular_income': True
            }
            
        except Exception as e:
            return False, {'error': str(e)}

    def verify_salary_slip(self, file_path: str) -> Tuple[bool, Dict]:
        """
        Verify and analyze salary slip
        """
        try:
            # Implement salary slip analysis logic here
            # This could include:
            # - OCR to extract text
            # - Verifying employer details
            # - Extracting salary components
            # For now, return a mock analysis
            
            return True, {
                'verified': True,
                'gross_salary': 60000,
                'net_salary': 48000,
                'employer_verified': True
            }
            
        except Exception as e:
            return False, {'error': str(e)}

    def _get_digilocker_token(self, auth_code: str) -> Dict:
        """
        Exchange authorization code for access token
        """
        payload = {
            'code': auth_code,
            'grant_type': 'authorization_code',
            'client_id': self.digilocker_client_id,
            'client_secret': self.digilocker_client_secret,
            'redirect_uri': self.digilocker_redirect_uri
        }
        
        response = requests.post(
            f"{self.digilocker_base_url}/token",
            data=payload
        )
        
        return response.json()

    def _fetch_aadhaar(self, access_token: str) -> Optional[Dict]:
        """
        Fetch Aadhaar details from DigiLocker
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(
            f"{self.digilocker_base_url}/documents/aadhaar",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        return None

    def _fetch_pan(self, access_token: str) -> Optional[Dict]:
        """
        Fetch PAN details from DigiLocker
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(
            f"{self.digilocker_base_url}/documents/pan",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        return None

    def _generate_state_token(self) -> str:
        """
        Generate a secure state token for OAuth flow
        """
        return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')

    def _hash_aadhaar(self, aadhaar_number: str) -> str:
        """
        Securely hash Aadhaar number
        """
        return hashlib.sha256(aadhaar_number.encode()).hexdigest()

    def _process_ekyc_data(self, data: Dict) -> Dict:
        """
        Process and structure eKYC response data
        """
        return {
            'verified': True,
            'aadhaar_number': data.get('aadhaar_number'),
            'name': data.get('name'),
            'dob': data.get('dob'),
            'gender': data.get('gender'),
            'address': {
                'street': data.get('address', {}).get('street'),
                'city': data.get('address', {}).get('city'),
                'state': data.get('address', {}).get('state'),
                'pincode': data.get('address', {}).get('pincode')
            },
            'photo_url': data.get('photo_url'),
            'verification_timestamp': datetime.utcnow().isoformat()
        }