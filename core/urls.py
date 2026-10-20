"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path
from legal_engine.views import simulate_api, generate_audit_pdf
from django.shortcuts import render

def dashboard_view(request):
    return render(request, 'dashboard.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),
    path('api/simulate/', simulate_api, name='simulate_api'),
    path('api/generate-pdf/', generate_audit_pdf, name='generate_audit_pdf'),
]