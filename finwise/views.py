from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt
@require_http_methods(["GET"])
def api_root(request):
    """
    API root endpoint that provides information about available endpoints
    """
    api_info = {
        "name": "Finwise API",
        "version": "1.0.0",
        "description": "Financial services API for micro and small enterprises",
        "endpoints": {
            "admin": "/admin/",
            "wallet": "/api/wallet/",
            "authentication": "/api/auth/",
            "mses": "/api/mses/",
            "markets": "/api/markets/",
            "reports": "/api/reports/",
            "dashboard": "/api/dashboard/",
            "loans": "/api/loans/",
            "kyc": "/api/kyc/",
            "customers": "/api/customers/",
            "payments": "/api/payments/",
            "marketplace": "/api/marketplace/",
            "shared": "/api/shared/"
        },
        "status": "active",
        "documentation": "Available at /api/docs/ (if configured)"
    }
    
    return JsonResponse(api_info, json_dumps_params={'indent': 2})
