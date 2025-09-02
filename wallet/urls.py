from django.urls import path
from .views import (
    WalletDetailView,
    WalletDepositView,
    WalletWithdrawView,
    WalletTransferView,
    WalletTransactionListView,
)

urlpatterns = [
    path('my-wallet/', WalletDetailView.as_view(), name='my-wallet'),
    path('deposit/', WalletDepositView.as_view(), name='wallet-deposit'),
    path('withdraw/', WalletWithdrawView.as_view(), name='wallet-withdraw'),
    path('transfer/', WalletTransferView.as_view(), name='wallet-transfer'),
    path('transactions/', WalletTransactionListView.as_view(), name='wallet-transactions'),
]
