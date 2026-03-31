from django import forms
from django.core.validators import RegexValidator

class ConsultationRequestForm(forms.Form):
    SERVICE_TYPE_CHOICES = [
        ('dental', 'Dental & Oral Surgery Anesthesia'),
        ('ambulatory', 'Ambulatory Surgical Center Support'),
        ('endoscopy', 'Endoscopy & GI Procedures'),
        ('pediatric', 'Pediatric Anesthesia'),
        ('other', 'Other Services'),
    ]
    
    CONTACT_METHOD_CHOICES = [
        ('phone', 'Phone'),
        ('email', 'Email'),
    ]
    
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your last name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your email address'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\-?\d{3}\-?\d{3}\-?\d{4}$',
                message="Please enter a valid phone number (e.g., 555-555-5555)"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your phone number'
        })
    )
    
    practice_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your practice or facility name'
        })
    )
    
    service_type = forms.ChoiceField(
        choices=SERVICE_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Please describe your anesthesia needs or any specific requirements...'
        })
    )
    
    preferred_contact = forms.ChoiceField(
        choices=CONTACT_METHOD_CHOICES,
        initial='phone',
        widget=forms.RadioSelect
    )
