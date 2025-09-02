from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Wallet, WalletTransaction
from .serializers import WalletSerializer, WalletTransactionSerializer

class WalletDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WalletSerializer

    def get_object(self):
        # Returns the wallet of the logged-in user
        return self.request.user.wallet


class WalletDepositView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError()
        except Exception:
            return Response({'detail': 'Invalid amount'}, status=400)
        with transaction.atomic():
            wallet = request.user.wallet
            wallet.balance = wallet.balance + amount
            wallet.save(update_fields=['balance'])
            WalletTransaction.objects.create(wallet=wallet, transaction_type='deposit', amount=amount)
        return Response({'detail': 'Deposit successful', 'balance': wallet.balance}, status=200)


class WalletWithdrawView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError()
        except Exception:
            return Response({'detail': 'Invalid amount'}, status=400)
        with transaction.atomic():
            wallet = request.user.wallet
            if wallet.balance < amount:
                return Response({'detail': 'Insufficient balance'}, status=400)
            wallet.balance = wallet.balance - amount
            wallet.save(update_fields=['balance'])
            WalletTransaction.objects.create(wallet=wallet, transaction_type='withdrawal', amount=amount)
        return Response({'detail': 'Withdrawal successful', 'balance': wallet.balance}, status=200)


class WalletTransferView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        to_username = request.data.get('to_username')
        amount = request.data.get('amount')
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError()
        except Exception:
            return Response({'detail': 'Invalid amount'}, status=400)

        User = get_user_model()
        try:
            recipient = User.objects.get(username=to_username)
            recipient_wallet = recipient.wallet
        except Exception:
            return Response({'detail': 'Recipient not found'}, status=404)

        with transaction.atomic():
            sender_wallet = request.user.wallet
            if sender_wallet.balance < amount:
                return Response({'detail': 'Insufficient balance'}, status=400)
            sender_wallet.balance = sender_wallet.balance - amount
            sender_wallet.save(update_fields=['balance'])
            recipient_wallet.balance = recipient_wallet.balance + amount
            recipient_wallet.save(update_fields=['balance'])
            WalletTransaction.objects.create(wallet=sender_wallet, transaction_type='transfer_out', amount=amount, reference=f"to:{to_username}")
            WalletTransaction.objects.create(wallet=recipient_wallet, transaction_type='transfer_in', amount=amount, reference=f"from:{request.user.username}")
        return Response({'detail': 'Transfer successful', 'balance': sender_wallet.balance}, status=200)


class WalletTransactionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WalletTransactionSerializer

    def get_queryset(self):
        return WalletTransaction.objects.filter(wallet=self.request.user.wallet)
