from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum
from mse.models import Wallet
from markets.models import Transaction as MarketTransaction
from loans.models import GroupLoan, GroupLoanRepayment
from .serializers import (
    CombinedReportSerializer, 
    IncomeReportSerializer, 
    WalletBalanceSerializer, 
    LoanReportSerializer
)

# ---------- Individual Report Views ----------

class IncomeReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        mse_id = request.query_params.get('mse')
        sales = MarketTransaction.objects.filter(mse_id=mse_id, type='sale').aggregate(total=Sum('amount'))['total'] or 0
        purchases = MarketTransaction.objects.filter(mse_id=mse_id, type='purchase').aggregate(total=Sum('amount'))['total'] or 0
        data = {'sales': sales, 'purchases': purchases, 'income': sales - purchases}
        serializer = IncomeReportSerializer(data)
        return Response(serializer.data)

class WalletBalanceReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        mse_id = request.query_params.get('mse')
        balance = Wallet.objects.filter(mse_id=mse_id).values_list('balance', flat=True).first() or 0
        serializer = WalletBalanceSerializer({'balance': balance})
        return Response(serializer.data)

class LoanReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        group_id = request.query_params.get('group')
        total_loans = GroupLoan.objects.filter(group_id=group_id).aggregate(total=Sum('amount'))['total'] or 0
        total_repayments = GroupLoanRepayment.objects.filter(loan__group_id=group_id).aggregate(total=Sum('amount'))['total'] or 0
        data = {
            'total_loans': total_loans,
            'total_repayments': total_repayments,
            'outstanding': total_loans - total_repayments
        }
        serializer = LoanReportSerializer(data)
        return Response(serializer.data)

# ---------- Combined Dashboard View ----------

class DashboardReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        mse_id = request.query_params.get('mse')
        group_id = request.query_params.get('group')

        # Income Report
        sales = MarketTransaction.objects.filter(mse_id=mse_id, type='sale').aggregate(total=Sum('amount'))['total'] or 0
        purchases = MarketTransaction.objects.filter(mse_id=mse_id, type='purchase').aggregate(total=Sum('amount'))['total'] or 0
        income_data = {'sales': sales, 'purchases': purchases, 'income': sales - purchases}

        # Wallet Balance
        balance = Wallet.objects.filter(mse_id=mse_id).values_list('balance', flat=True).first() or 0
        wallet_data = {'balance': balance}

        # Loan Report
        total_loans = GroupLoan.objects.filter(group_id=group_id).aggregate(total=Sum('amount'))['total'] or 0
        total_repayments = GroupLoanRepayment.objects.filter(loan__group_id=group_id).aggregate(total=Sum('amount'))['total'] or 0
        loan_data = {
            'total_loans': total_loans,
            'total_repayments': total_repayments,
            'outstanding': total_loans - total_repayments
        }

        combined_data = {
            'income_report': income_data,
            'wallet_balance': wallet_data,
            'loan_report': loan_data
        }

        serializer = CombinedReportSerializer(combined_data)
        return Response(serializer.data)
