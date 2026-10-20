from django.urls import path
from .views import simulate_api, generate_audit_pdf

urlpatterns = [
    path('simulate/', simulate_api, name='simulate_api'),
    path('generate-pdf/', generate_audit_pdf, name='generate_audit_pdf'),
]