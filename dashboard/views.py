from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Sum, Count, Avg
from django.utils import timezone


def dashboard_home(request):
    """Basic dashboard home view"""
    return JsonResponse({
        'message': 'Dashboard module is available',
        'status': 'success'
    })


@csrf_exempt
def dashboard_overview(request):
    """Basic dashboard overview endpoint"""
    return JsonResponse({
        'message': 'Dashboard overview functionality',
        'timestamp': timezone.now().isoformat(),
        'status': 'success'
    })
