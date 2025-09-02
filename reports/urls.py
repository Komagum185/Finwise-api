from django.urls import path
from .views import (
    IncomeReportView, 
    WalletBalanceReportView, 
    LoanReportView, 
    DashboardReportView
)

urlpatterns = [
    # Individual endpoints
    path('income/', IncomeReportView.as_view(), name='income-report'),
    path('wallet/', WalletBalanceReportView.as_view(), name='wallet-report'),
    path('loan/', LoanReportView.as_view(), name='loan-report'),

    # Combined dashboard endpoint
    path('dashboard/', DashboardReportView.as_view(), name='dashboard-report'),
]
