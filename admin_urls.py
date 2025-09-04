from django.urls import path, include
from rest_framework.routers import DefaultRouter
from admin_views import SuperAdminUserViewSet, SuperAdminMSEViewSet, SuperAdminReportViewSet

# Create routers for each viewset
user_router = DefaultRouter()
user_router.register(r'users', SuperAdminUserViewSet, basename='admin-user')

mse_router = DefaultRouter()
mse_router.register(r'mse', SuperAdminMSEViewSet, basename='admin-mse')

report_router = DefaultRouter()
report_router.register(r'reports', SuperAdminReportViewSet, basename='admin-report')

urlpatterns = [
    # User management
    path('', include(user_router.urls)),
    
    # MSE management
    path('', include(mse_router.urls)),
    
    # Reports and analytics
    path('', include(report_router.urls)),
]
