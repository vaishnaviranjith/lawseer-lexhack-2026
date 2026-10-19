"""
URL routing for the legal_engine app.
"""
from django.urls import path
from .views import dashboard_view, SimulateConsequenceView

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('api/simulate/', SimulateConsequenceView.as_view(), name='simulate-consequences'),
]