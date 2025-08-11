from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Sum, Count, Avg
from django.utils import timezone


def reports_home(request):
    """Basic reports home view"""
    return JsonResponse({
        'message': 'Reports module is available',
        'status': 'success'
    })


@csrf_exempt
def basic_report(request):
    """Basic report endpoint"""
    return JsonResponse({
        'message': 'Basic report functionality',
        'timestamp': timezone.now().isoformat(),
        'status': 'success'
    })
