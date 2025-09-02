from rest_framework import serializers
from .models import LoanProduct, GroupLoan, GroupLoanRepayment


class LoanProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanProduct
        fields = ['id', 'name', 'interest_rate', 'max_amount', 'repayment_period_months', 'is_active', 'created_at']


class GroupLoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupLoan
        fields = ['id', 'group', 'product', 'amount', 'status', 'approved_by', 'approved_at', 'disbursed_at', 'created_at']
        read_only_fields = ['status', 'approved_by', 'approved_at', 'disbursed_at', 'created_at']


class GroupLoanRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupLoanRepayment
        fields = ['id', 'loan', 'amount', 'repaid_at']
        read_only_fields = ['repaid_at']


