from django.urls import path, include
from rest_framework.routers import DefaultRouter
from mse_views import MSEWalletViewSet, MSELoanViewSet, MSECustomerViewSet, MSESupplierViewSet, MSETransactionViewSet, MSEReportViewSet

# Create routers for each viewset
wallet_router = DefaultRouter()
wallet_router.register(r'wallet', MSEWalletViewSet, basename='mse-wallet')

loan_router = DefaultRouter()
loan_router.register(r'loans', MSELoanViewSet, basename='mse-loan')

customer_router = DefaultRouter()
customer_router.register(r'customers', MSECustomerViewSet, basename='mse-customer')

supplier_router = DefaultRouter()
supplier_router.register(r'suppliers', MSESupplierViewSet, basename='mse-supplier')

transaction_router = DefaultRouter()
transaction_router.register(r'transactions', MSETransactionViewSet, basename='mse-transaction')

report_router = DefaultRouter()
report_router.register(r'reports', MSEReportViewSet, basename='mse-report')

urlpatterns = [
    # Wallet management
    path('', include(wallet_router.urls)),
    
    # Loan management
    path('', include(loan_router.urls)),
    
    # Customer management
    path('', include(customer_router.urls)),
    
    # Supplier management
    path('', include(supplier_router.urls)),
    
    # Transaction history
    path('', include(transaction_router.urls)),
    
    # Reports and analytics
    path('', include(report_router.urls)),
]
