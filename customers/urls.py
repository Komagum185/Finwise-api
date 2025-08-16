from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, CustomerFeedbackViewSet, SMSCampaignViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'feedback', CustomerFeedbackViewSet, basename='customer-feedback')
router.register(r'sms-campaigns', SMSCampaignViewSet, basename='sms-campaign')

urlpatterns = [
    path('', include(router.urls)),
]
