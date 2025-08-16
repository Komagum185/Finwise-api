from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Enhanced Wallet endpoints (matching TypeScript interfaces)
router.register(r'enhanced-wallets', views.EnhancedWalletViewSet)
router.register(r'enhanced-wallet-transactions', views.EnhancedWalletTransactionViewSet)
router.register(r'wallet-transfers', views.WalletTransferViewSet)
router.register(r'wallet-statistics', views.WalletStatisticsViewSet)

# Legacy endpoints (for backward compatibility)
router.register(r'categories', views.CategoryViewSet)
router.register(r'wallets', views.WalletViewSet)
router.register(r'wallet-transactions', views.WalletTransactionViewSet)
router.register(r'transactions', views.TransactionViewSet)
router.register(r'budgets', views.BudgetViewSet)
router.register(r'goals', views.GoalViewSet)

# Payment Transaction endpoints
router.register(r'payment-transactions', views.PaymentTransactionViewSet, basename='payment-transaction')
router.register(r'bulk-payments', views.BulkPaymentViewSet, basename='bulk-payment')
router.register(r'bulk-payment-recipients', views.BulkPaymentRecipientViewSet, basename='bulk-payment-recipient')

app_name = 'wallet'

urlpatterns = [
    path('', include(router.urls)),
]

