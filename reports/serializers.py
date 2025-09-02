# reports/serializers.py
from rest_framework import serializers

class IncomeReportSerializer(serializers.Serializer):
    sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    purchases = serializers.DecimalField(max_digits=12, decimal_places=2)
    income = serializers.DecimalField(max_digits=12, decimal_places=2)

class WalletBalanceSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)

class LoanReportSerializer(serializers.Serializer):
    total_loans = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_repayments = serializers.DecimalField(max_digits=12, decimal_places=2)
    outstanding = serializers.DecimalField(max_digits=12, decimal_places=2)

class CombinedReportSerializer(serializers.Serializer):
    income_report = IncomeReportSerializer()
    wallet_balance = WalletBalanceSerializer()
    loan_report = LoanReportSerializer()
