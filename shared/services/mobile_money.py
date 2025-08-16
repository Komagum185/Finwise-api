import requests
import json
import hashlib
import hmac
import time
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.cache import cache
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class MobileMoneyService:
    """Base mobile money service class"""
    
    def __init__(self, provider: str):
        self.provider = provider
        self.api_key = getattr(settings, f'{provider.upper()}_API_KEY', '')
        self.api_secret = getattr(settings, f'{provider.upper()}_API_SECRET', '')
        self.base_url = getattr(settings, f'{provider.upper()}_BASE_URL', '')
        self.merchant_id = getattr(settings, f'{provider.upper()}_MERCHANT_ID', '')
        
    def _generate_signature(self, data: str) -> str:
        """Generate HMAC signature for API requests"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, endpoint: str, method: str = 'POST', data: Dict = None) -> Dict:
        """Make HTTP request to mobile money API"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-Timestamp': str(int(time.time())),
        }
        
        if data:
            data_str = json.dumps(data, sort_keys=True)
            headers['X-Signature'] = self._generate_signature(data_str)
        
        try:
            if method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                response = requests.get(url, headers=headers, timeout=30)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Mobile money API request failed: {e}")
            raise MobileMoneyAPIError(f"API request failed: {str(e)}")
    
    def initiate_payment(self, amount: Decimal, phone_number: str, reference: str, 
                        description: str = "") -> Dict[str, Any]:
        """Initiate a payment request"""
        raise NotImplementedError("Subclasses must implement initiate_payment")
    
    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Verify payment status"""
        raise NotImplementedError("Subclasses must implement verify_payment")
    
    def refund_payment(self, transaction_id: str, amount: Decimal, reason: str = "") -> Dict[str, Any]:
        """Refund a payment"""
        raise NotImplementedError("Subclasses must implement refund_payment")


class MTNMoMoService(MobileMoneyService):
    """MTN Mobile Money service implementation"""
    
    def __init__(self):
        super().__init__('mtn')
    
    def initiate_payment(self, amount: Decimal, phone_number: str, reference: str, 
                        description: str = "") -> Dict[str, Any]:
        """Initiate MTN MoMo payment"""
        endpoint = "/collection/v1_0/requesttopay"
        
        data = {
            "amount": str(amount),
            "currency": "UGX",
            "externalId": reference,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone_number
            },
            "payerMessage": description,
            "payeeNote": f"Payment for {reference}"
        }
        
        # First, get access token
        token = self._get_access_token()
        
        # Make payment request
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Reference-Id': reference,
            'X-Target-Environment': 'sandbox',  # Change to 'live' for production
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            return {
                'status': 'success',
                'transaction_id': reference,
                'message': 'Payment request initiated successfully'
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"MTN MoMo payment initiation failed: {e}")
            return {
                'status': 'error',
                'message': f'Payment initiation failed: {str(e)}'
            }
    
    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Verify MTN MoMo payment status"""
        endpoint = f"/collection/v1_0/requesttopay/{transaction_id}"
        
        # Get access token
        token = self._get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Target-Environment': 'sandbox',  # Change to 'live' for production
        }
        
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'status': 'success',
                'transaction_id': transaction_id,
                'payment_status': data.get('status', 'unknown'),
                'amount': data.get('amount'),
                'currency': data.get('currency'),
                'payer': data.get('payer', {}).get('partyId'),
                'timestamp': data.get('financialTransactionId')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"MTN MoMo payment verification failed: {e}")
            return {
                'status': 'error',
                'message': f'Payment verification failed: {str(e)}'
            }
    
    def _get_access_token(self) -> str:
        """Get MTN MoMo access token"""
        cache_key = f"mtn_momo_token_{self.merchant_id}"
        token = cache.get(cache_key)
        
        if token:
            return token
        
        endpoint = "/collection/token/"
        
        # Create basic auth header
        import base64
        auth_string = f"{self.api_key}:{self.api_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'X-Reference-Id': str(int(time.time())),
            'X-Target-Environment': 'sandbox',  # Change to 'live' for production
        }
        
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            token = data.get('access_token')
            
            if token:
                # Cache token for 1 hour (MTN tokens typically expire in 1 hour)
                cache.set(cache_key, token, 3600)
                return token
            else:
                raise MobileMoneyAPIError("Failed to get access token")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"MTN MoMo token request failed: {e}")
            raise MobileMoneyAPIError(f"Token request failed: {str(e)}")


class AirtelMoneyService(MobileMoneyService):
    """Airtel Money service implementation"""
    
    def __init__(self):
        super().__init__('airtel')
    
    def initiate_payment(self, amount: Decimal, phone_number: str, reference: str, 
                        description: str = "") -> Dict[str, Any]:
        """Initiate Airtel Money payment"""
        endpoint = "/merchant/v1/payments/"
        
        data = {
            "reference": reference,
            "subscriber": {
                "country": "UG",
                "currency": "UGX",
                "msisdn": phone_number
            },
            "transaction": {
                "amount": str(amount),
                "country": "UG",
                "currency": "UGX",
                "id": reference
            }
        }
        
        try:
            response = self._make_request(endpoint, 'POST', data)
            
            return {
                'status': 'success',
                'transaction_id': reference,
                'message': 'Payment request initiated successfully',
                'data': response
            }
            
        except Exception as e:
            logger.error(f"Airtel Money payment initiation failed: {e}")
            return {
                'status': 'error',
                'message': f'Payment initiation failed: {str(e)}'
            }
    
    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Verify Airtel Money payment status"""
        endpoint = f"/standard/v1/payments/{transaction_id}"
        
        try:
            response = self._make_request(endpoint, 'GET')
            
            return {
                'status': 'success',
                'transaction_id': transaction_id,
                'payment_status': response.get('status', 'unknown'),
                'amount': response.get('amount'),
                'currency': response.get('currency'),
                'payer': response.get('payer', {}).get('msisdn'),
                'timestamp': response.get('timestamp')
            }
            
        except Exception as e:
            logger.error(f"Airtel Money payment verification failed: {e}")
            return {
                'status': 'error',
                'message': f'Payment verification failed: {str(e)}'
            }


class MobileMoneyFactory:
    """Factory class for creating mobile money service instances"""
    
    @staticmethod
    def get_service(provider: str) -> MobileMoneyService:
        """Get mobile money service instance based on provider"""
        providers = {
            'mtn': MTNMoMoService,
            'airtel': AirtelMoneyService,
        }
        
        service_class = providers.get(provider.lower())
        if not service_class:
            raise ValueError(f"Unsupported mobile money provider: {provider}")
        
        return service_class()


class MobileMoneyAPIError(Exception):
    """Custom exception for mobile money API errors"""
    pass


# Utility functions for mobile money operations
def initiate_mobile_money_payment(provider: str, amount: Decimal, phone_number: str, 
                                 reference: str, description: str = "") -> Dict[str, Any]:
    """Utility function to initiate mobile money payment"""
    try:
        service = MobileMoneyFactory.get_service(provider)
        return service.initiate_payment(amount, phone_number, reference, description)
    except Exception as e:
        logger.error(f"Mobile money payment initiation failed: {e}")
        return {
            'status': 'error',
            'message': f'Payment initiation failed: {str(e)}'
        }


def verify_mobile_money_payment(provider: str, transaction_id: str) -> Dict[str, Any]:
    """Utility function to verify mobile money payment"""
    try:
        service = MobileMoneyFactory.get_service(provider)
        return service.verify_payment(transaction_id)
    except Exception as e:
        logger.error(f"Mobile money payment verification failed: {e}")
        return {
            'status': 'error',
            'message': f'Payment verification failed: {str(e)}'
        }


def get_supported_providers() -> list:
    """Get list of supported mobile money providers"""
    return ['mtn', 'airtel']


def validate_phone_number(phone_number: str, provider: str = None) -> bool:
    """Validate phone number format for mobile money"""
    import re
    
    # Remove any non-digit characters
    clean_number = re.sub(r'\D', '', phone_number)
    
    # Basic validation for Uganda phone numbers
    if clean_number.startswith('256'):
        clean_number = clean_number[3:]
    elif clean_number.startswith('0'):
        clean_number = clean_number[1:]
    
    # Check if it's a valid Uganda mobile number
    if len(clean_number) == 9 and clean_number.startswith(('7', '3')):
        return True
    
    return False
