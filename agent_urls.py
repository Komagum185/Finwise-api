from django.urls import path, include
from rest_framework.routers import DefaultRouter
from agent_views import AgentMSEViewSet, AgentWalletViewSet, AgentRegistrationViewSet, AgentReportViewSet

# Create routers for each viewset
mse_router = DefaultRouter()
mse_router.register(r'mse', AgentMSEViewSet, basename='agent-mse')

wallet_router = DefaultRouter()
wallet_router.register(r'wallets', AgentWalletViewSet, basename='agent-wallet')

registration_router = DefaultRouter()
registration_router.register(r'registrations', AgentRegistrationViewSet, basename='agent-registration')

report_router = DefaultRouter()
report_router.register(r'reports', AgentReportViewSet, basename='agent-report')

urlpatterns = [
    # MSE management
    path('', include(mse_router.urls)),
    
    # Wallet monitoring
    path('', include(wallet_router.urls)),
    
    # Registration tracking
    path('', include(registration_router.urls)),
    
    # Reports and analytics
    path('', include(report_router.urls)),
]
