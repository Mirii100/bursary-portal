import uuid
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class MpesaClient:
    """
    Mock M-Pesa API Client for the Bursary Management System.
    In a real application, this would use the Daraja API.
    """
    @staticmethod
    def initiate_b2c_payment(phone, amount, occasion="Bursary"):
        """
        Simulates a Business to Customer (B2C) payment.
        """
        # Simulate API delay/logic
        transaction_id = f"MPESA{uuid.uuid4().hex[:8].upper()}"
        
        # In reality, you'd send a request to Safaricom
        logger.info(f"M-PESA B2C: Sending KES {amount} to {phone} for {occasion}. Ref: {transaction_id}")
        
        # Return a mock response
        return {
            'status': 'Success',
            'transaction_id': transaction_id,
            'timestamp': timezone.now(),
            'message': 'Payment processed successfully'
        }

def process_bursary_disbursement(application):
    """
    Helper function to handle the payment logic.
    """
    from .models import Payment
    
    phone = application.student.phone
    amount = application.amount_requested
    
    # Check if student has a phone number
    if not phone:
        return False, "Student does not have a registered phone number for M-Pesa."
        
    # Initiate M-Pesa Payment
    mpesa = MpesaClient()
    response = mpesa.initiate_b2c_payment(phone, amount)
    
    if response['status'] == 'Success':
        # Create Payment Record
        Payment.objects.create(
            application=application,
            amount_awarded=amount,
            payment_reference=response['transaction_id']
        )
        return True, response['transaction_id']
    
    return False, "M-Pesa payment failed."
