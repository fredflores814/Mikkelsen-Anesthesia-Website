from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("services/", views.services, name="services"),
    path("financial-policy/", views.financial_policy, name="financial_policy"),
    path("faq/", views.faq, name="faq"),
    path("contact/", views.contact, name="contact"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("payment/", views.payment, name="payment"),
    path("payment/success/<int:payment_id>/", views.payment_success, name="payment_success"),
]
