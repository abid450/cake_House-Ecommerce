# payment/sslcommerz.py

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class SSLCommerzPayment:
    """SSLCommerz Payment Gateway Helper"""
    
    def __init__(self):
        self.store_id = settings.SSLCOMMERZ_STORE_ID
        self.store_passwd = settings.SSLCOMMERZ_STORE_PASSWORD
        self.is_sandbox = settings.SSLCOMMERZ_IS_SANDBOX
        
        if self.is_sandbox:
            self.base_url = 'https://sandbox.sslcommerz.com'
        else:
            self.base_url = 'https://securepay.sslcommerz.com'
    
    def get_session_url(self):
        return f'{self.base_url}/gwprocess/v4/api.php'
    
    def get_validation_url(self):
        return f'{self.base_url}/validator/api/validationserverAPI.php'
    
    def get_refund_url(self):
        return f'{self.base_url}/validator/api/merchantTransIDvalidationAPI.php'
    
    def initiate_payment(self, order, request):
        """Initiate payment session with SSLCommerz"""
        
        success_url = settings.PAYMENT_SUCCESS_URL
        fail_url = settings.PAYMENT_FAIL_URL
        cancel_url = settings.PAYMENT_CANCEL_URL
        ipn_url = settings.PAYMENT_IPN_URL
        
        # ✅ Customer Info
        cus_name = order.shipping_name or (order.user.full_name if order.user else 'Guest')
        cus_email = order.shipping_email or (order.user.email if order.user else 'guest@example.com')
        cus_phone = order.shipping_phone or (order.user.phone if order.user else '01700000000')
        cus_add1 = order.shipping_address or 'N/A'
        cus_city = order.shipping_city or 'Dhaka'
        cus_state = order.shipping_state or order.shipping_city or 'Dhaka'
        cus_postcode = order.shipping_postal_code or '1000'
        cus_country = order.shipping_country or 'Bangladesh'
        
        # ✅ Shipping Info (Same as Customer)
        ship_name = cus_name
        ship_add1 = cus_add1
        ship_city = cus_city
        ship_state = cus_state
        ship_postcode = cus_postcode
        ship_country = cus_country
        
        # ✅ Product Info
        product_names = ', '.join([item.product_name for item in order.items.all()[:5]])
        if order.items.count() > 5:
            product_names += f' + {order.items.count() - 5} more'
        
        # ✅ Complete Payload
        payload = {
            # Store
            'store_id': self.store_id,
            'store_passwd': self.store_passwd,
            'total_amount': str(order.total_amount),
            'currency': 'BDT',
            'tran_id': str(order.id),
            
            # URLs
            'success_url': success_url,
            'fail_url': fail_url,
            'cancel_url': cancel_url,
            'ipn_url': ipn_url,
            
            # Customer Info
            'cus_name': cus_name,
            'cus_email': cus_email,
            'cus_add1': cus_add1,
            'cus_add2': '',
            'cus_city': cus_city,
            'cus_state': cus_state,
            'cus_postcode': cus_postcode,
            'cus_country': cus_country,
            'cus_phone': cus_phone,
            'cus_fax': '',
            
            # ✅ Shipping Info (REQUIRED!)
            'ship_name': ship_name,
            'ship_add1': ship_add1,
            'ship_add2': '',
            'ship_city': ship_city,
            'ship_state': ship_state,
            'ship_postcode': ship_postcode,
            'ship_country': ship_country,
            
            # Product Info
            'product_name': product_names,
            'product_category': 'Bakery',
            'product_profile': 'general',
            
            # Shipping Method
            'shipping_method': 'Courier',
            'num_of_item': order.total_items,
            
            # Additional
            'value_a': str(order.order_number),
            'value_b': str(order.user.id) if order.user else 'guest',
        }
        
        try:
            response = requests.post(
                self.get_session_url(),
                data=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"SSLCommerz initiate response: {result}")
            
            if result.get('status') == 'SUCCESS':
                return {
                    'success': True,
                    'gateway_url': result.get('GatewayPageURL'),
                    'session_key': result.get('sessionkey'),
                    'transaction_id': result.get('tran_id'),
                }
            else:
                return {
                    'success': False,
                    'error': result.get('failedreason', 'Payment initiation failed'),
                    'raw': result,
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"SSLCommerz request failed: {str(e)}")
            return {
                'success': False,
                'error': f'Payment gateway error: {str(e)}',
            }
    
    def validate_payment(self, val_id):
        """Validate payment with SSLCommerz"""
        params = {
            'val_id': val_id,
            'store_id': self.store_id,
            'store_passwd': self.store_passwd,
            'format': 'json',
        }
        
        try:
            response = requests.get(
                self.get_validation_url(),
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"SSLCommerz validation response: {result}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"SSLCommerz validation failed: {str(e)}")
            return {'status': 'FAILED', 'error': str(e)}
    
    def initiate_refund(self, bank_tran_id, refund_amount, refund_remarks=''):
        """Initiate refund"""
        params = {
            'bank_tran_id': bank_tran_id,
            'store_id': self.store_id,
            'store_passwd': self.store_passwd,
            'refund_amount': str(refund_amount),
            'refund_remarks': refund_remarks,
            'format': 'json',
        }
        
        try:
            response = requests.get(
                f'{self.base_url}/validator/api/merchantTransIDvalidationAPI.php',
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"SSLCommerz refund failed: {str(e)}")
            return {'status': 'FAILED', 'error': str(e)}


# Singleton instance
sslcommerz = SSLCommerzPayment()