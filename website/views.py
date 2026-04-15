from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import logging
from .forms import ConsultationRequestForm, PaymentForm
from .models import Payment

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'website/home.html')

def services(request):
    return render(request, 'website/services.html')

def financial_policy(request):
    return render(request, 'website/financial_policy.html')

def faq(request):
    return render(request, 'website/faq.html')

def privacy_policy(request):
    return render(request, 'website/privacy_policy.html')

def contact(request):
    if request.method == 'POST':
        form = ConsultationRequestForm(request.POST)
        if form.is_valid():
            # Extract form data
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            practice_name = form.cleaned_data['practice_name']
            service_type = form.cleaned_data['service_type']
            message = form.cleaned_data['message']
            preferred_contact = form.cleaned_data['preferred_contact']
            
            # Get service type display name
            service_type_display = dict(ConsultationRequestForm.SERVICE_TYPE_CHOICES).get(service_type, service_type)
            
            # Create email content
            subject = f'New Consultation Request: {first_name} {last_name}'
            
            email_content = f"""
New Consultation Request Received

Client Information:
- Name: {first_name} {last_name}
- Email: {email}
- Phone: {phone}
- Practice/Facility: {practice_name or 'Not provided'}
- Service Type: {service_type_display}
- Preferred Contact Method: {preferred_contact.title()}

Additional Information:
{message or 'No additional information provided'}

---
This consultation request was submitted via the Mikkelsen Anesthesia website.
            """
            
            # Send email to admin
            try:
                send_mail(
                    subject=subject,
                    message=email_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_EMAIL],
                    fail_silently=False,
                )
                
                # Send confirmation email to client
                confirmation_subject = 'Your Consultation Request - Mikkelsen Anesthesia'
                confirmation_content = f"""
Dear {first_name} {last_name},

Thank you for your interest in Mikkelsen Anesthesia services. We have received your consultation request and will contact you within 24 hours to discuss your anesthesia needs.

Your Request Details:
- Service Type: {service_type_display}
- Preferred Contact Method: {preferred_contact.title()}

If you need to reach us immediately, please call us at (608) 865-0971.

Best regards,
The Mikkelsen Anesthesia Team
ErikMikkelsen@mikkelsenanesthesia.com
                """
                
                send_mail(
                    subject=confirmation_subject,
                    message=confirmation_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Thank you! Your consultation request has been submitted successfully. We will contact you within 24 hours.')
                
            except Exception as e:
                messages.error(request, 'There was an error sending your request. Please try again or call us directly at (608) 865-0971.')
                
            return render(request, 'website/contact.html', {'form': ConsultationRequestForm()})
    else:
        form = ConsultationRequestForm()
    
    return render(request, 'website/contact.html', {'form': form})

def payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                # Create payment record
                payment = form.save(commit=False)
                payment.status = 'pending'
                payment.save()
                
                # Process payment with Authorize.net
                result = process_authorize_net_payment(payment, form.cleaned_data)
                
                if result['success']:
                    payment.transaction_id = result['transaction_id']
                    payment.auth_code = result['auth_code']
                    payment.status = 'approved'
                    payment.save()
                    
                    # Send confirmation email
                    send_payment_confirmation_email(payment)
                    
                    messages.success(request, 'Payment processed successfully!')
                    return redirect('payment_success', payment_id=payment.id)
                else:
                    payment.status = 'declined'
                    payment.save()
                    messages.error(request, f"Payment failed: {result['error_message']}")
                    
            except Exception as e:
                logger.error(f"Payment processing error: {str(e)}")
                if 'payment' in locals():
                    payment.status = 'error'
                    payment.save()
                messages.error(request, 'An error occurred while processing your payment. Please try again.')
    else:
        form = PaymentForm()
    
    return render(request, 'website/payment.html', {'form': form})

def payment_success(request, payment_id):
    try:
        payment = Payment.objects.get(id=payment_id)
        return render(request, 'website/payment_success.html', {'payment': payment})
    except Payment.DoesNotExist:
        messages.error(request, 'Payment record not found.')
        return redirect('payment')

def process_authorize_net_payment(payment, form_data):
    """Process payment using Authorize.net API"""
    try:
        from authorizenet import apicontractsv1
        from authorizenet.apicontrollers import createTransactionController
        from decimal import Decimal
        
        # Set up merchant authentication
        merchantAuth = apicontractsv1.merchantAuthenticationType()
        merchantAuth.name = settings.AUTHORIZE_NET_API_LOGIN_ID
        merchantAuth.transactionKey = settings.AUTHORIZE_NET_TRANSACTION_KEY
        
        # Set up credit card
        creditCard = apicontractsv1.creditCardType()
        creditCard.cardNumber = form_data['card_number'].replace(' ', '')
        creditCard.expirationDate = form_data['expiration_date'].replace('/', '')
        creditCard.cardCode = form_data['cvv']
        
        # Add credit card to payment type
        paymentType = apicontractsv1.paymentType()
        paymentType.creditCard = creditCard
        
        # Set up transaction request
        transactionRequest = apicontractsv1.transactionRequestType()
        transactionRequest.transactionType = apicontractsv1.transactionTypeEnum.authCaptureTransaction
        transactionRequest.amount = str(payment.amount)
        transactionRequest.payment = paymentType
        
        # Set up order
        order = apicontractsv1.orderType()
        order.invoiceNumber = f"INV-{payment.id}"
        order.description = payment.description or f"Payment from {payment.first_name} {payment.last_name}"
        transactionRequest.order = order
        
        # Set up customer info
        customer = apicontractsv1.customerType()
        customer.email = payment.email
        transactionRequest.customer = customer
        
        # Set up bill to
        billTo = apicontractsv1.customerAddressType()
        billTo.firstName = payment.first_name
        billTo.lastName = payment.last_name
        transactionRequest.billTo = billTo
        
        # Create transaction request
        createRequest = apicontractsv1.createTransactionRequest()
        createRequest.merchantAuthentication = merchantAuth
        createRequest.transactionRequest = transactionRequest
        
        # Create controller and get response
        controller = createTransactionController(createRequest)
        controller.setenvironment(settings.AUTHORIZE_NET_ENVIRONMENT)
        
        response = controller.execute()
        
        if response is not None:
            if hasattr(response.messages, 'resultCode') and response.messages.resultCode == 'Ok':
                transactionResponse = response.transactionResponse
                if transactionResponse.responseCode == '1':  # Approved
                    return {
                        'success': True,
                        'transaction_id': transactionResponse.transId,
                        'auth_code': transactionResponse.authCode
                    }
                else:
                    return {
                        'success': False,
                        'error_message': transactionResponse.errors.error[0].text if transactionResponse.errors else 'Transaction declined'
                    }
            else:
                return {
                    'success': False,
                    'error_message': response.messages.message[0].text if response.messages else 'Unknown error'
                }
        else:
            return {
                'success': False,
                'error_message': 'No response from payment gateway'
            }
            
    except Exception as e:
        logger.error(f"Authorize.net API error: {str(e)}")
        return {
            'success': False,
            'error_message': 'Payment processing failed'
        }

def send_payment_confirmation_email(payment):
    """Send payment confirmation email to client and admin"""
    try:
        # Email to admin
        admin_subject = f'Payment Received: {payment.first_name} {payment.last_name} - ${payment.amount}'
        admin_content = f"""
Payment Details:
- Name: {payment.first_name} {payment.last_name}
- Email: {payment.email}
- Phone: {payment.phone}
- Practice: {payment.practice_name or 'Not provided'}
- Amount: ${payment.amount}
- Transaction ID: {payment.transaction_id}
- Auth Code: {payment.auth_code}
- Description: {payment.description or 'No description'}

Payment was successfully processed via Authorize.net.
        """
        
        send_mail(
            subject=admin_subject,
            message=admin_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=False,
        )
        
        # Confirmation email to client
        client_subject = 'Payment Confirmation - Mikkelsen Anesthesia'
        client_content = f"""
Dear {payment.first_name} {payment.last_name},

Thank you for your payment to Mikkelsen Anesthesia.

Payment Details:
- Amount: ${payment.amount}
- Transaction ID: {payment.transaction_id}
- Date: {payment.created_at.strftime('%B %d, %Y at %I:%M %p')}

If you have any questions about this payment, please contact us at:
Email: ErikMikkelsen@mikkelsenanesthesia.com
Phone: (608) 865-0971

Best regards,
The Mikkelsen Anesthesia Team
        """
        
        send_mail(
            subject=client_subject,
            message=client_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.email],
            fail_silently=False,
        )
        
    except Exception as e:
        logger.error(f"Failed to send payment confirmation email: {str(e)}")
