from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .forms import ConsultationRequestForm

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
