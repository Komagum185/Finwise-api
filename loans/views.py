from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from authentication import models
from groups.models import GroupWallet
from .models import LoanProduct, GroupLoan, GroupLoanRepayment
from .serializers import LoanProductSerializer, GroupLoanSerializer, GroupLoanRepaymentSerializer


class LoanProductViewSet(viewsets.ModelViewSet):
    queryset = LoanProduct.objects.all()
    serializer_class = LoanProductSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupLoanViewSet(viewsets.ModelViewSet):
    queryset = GroupLoan.objects.all()
    serializer_class = GroupLoanSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        loan = self.get_object()
        if loan.status != 'pending':
            return Response({'detail': 'Loan cannot be approved'}, status=400)
        loan.status = 'approved'
        loan.approved_by = request.user
        loan.approved_at = timezone.now()
        loan.save(update_fields=['status', 'approved_by', 'approved_at'])
        return Response({'detail': 'Loan approved'}, status=200)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def disburse(self, request, pk=None):
        loan = self.get_object()
        if loan.status != 'approved':
            return Response({'detail': 'Loan cannot be disbursed'}, status=400)
        with transaction.atomic():
            wallet = GroupWallet.objects.get(group=loan.group)
            wallet.balance = wallet.balance + loan.amount
            wallet.save(update_fields=['balance'])
            loan.status = 'disbursed'
            loan.disbursed_at = timezone.now()
            loan.save(update_fields=['status', 'disbursed_at'])
        return Response({'detail': 'Loan disbursed', 'group_wallet_balance': wallet.balance}, status=200)


class GroupLoanRepaymentViewSet(viewsets.ModelViewSet):
    queryset = GroupLoanRepayment.objects.all()
    serializer_class = GroupLoanRepaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def repay(self, request):
        serializer = GroupLoanRepaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan = serializer.validated_data['loan']
        amount = serializer.validated_data['amount']

        if loan.status != 'disbursed':
            return Response({'detail': 'Loan is not disbursed'}, status=400)

        with transaction.atomic():
            repayment = serializer.save()
            wallet = GroupWallet.objects.get(group=loan.group)
            if wallet.balance < amount:
                return Response({'detail': 'Insufficient group wallet balance'}, status=400)
            wallet.balance = wallet.balance - amount
            wallet.save(update_fields=['balance'])

            # If fully repaid
            total_repaid = loan.repayments.aggregate(total=models.Sum('amount'))['total'] or 0
            if total_repaid >= loan.amount:
                loan.status = 'repaid'
                loan.save(update_fields=['status'])

        return Response({'detail': 'Repayment recorded', 'group_wallet_balance': wallet.balance}, status=201)


