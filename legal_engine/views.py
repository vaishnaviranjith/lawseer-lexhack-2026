"""
Views and API endpoints for legal consequence simulation.
"""
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import LegalRiskEngine

def dashboard_view(request):
    """Renders the executive decision workspace UI."""
    return render(request, 'dashboard.html')

class SimulateConsequenceView(APIView):
    """API endpoint providing instant counterfactual analysis."""
    def post(self, request):
        case_facts = request.data
        engine = LegalRiskEngine(case_facts)
        results = engine.run_full_comparison()
        return Response(results, status=status.HTTP_200_OK)