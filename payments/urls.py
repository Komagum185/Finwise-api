from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentProviderViewSet, QRPaymentViewSet, 
    ScheduledTransferViewSet, PaymentTransactionViewSet
)

router = DefaultRouter()
router.register(r'providers', PaymentProviderViewSet, basename='payment-provider')
router.register(r'qr-payments', QRPaymentViewSet, basename='qr-payment')
router.register(r'scheduled-transfers', ScheduledTransferViewSet, basename='scheduled-transfer')
router.register(r'transactions', PaymentTransactionViewSet, basename='payment-transaction')

urlpatterns = [
    path('', include(router.urls)),
]
