from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Group, GroupMembership, GroupWallet
from .serializers import GroupSerializer, GroupMembershipSerializer, GroupWalletSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def create_wallet(self, request, pk=None):
        group = self.get_object()
        if hasattr(group, 'wallet'):
            return Response({'detail': 'Wallet already exists'}, status=400)
        GroupWallet.objects.create(group=group)
        return Response({'detail': 'Wallet created'}, status=201)


class GroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = GroupMembership.objects.all()
    serializer_class = GroupMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupWalletViewSet(viewsets.ModelViewSet):
    queryset = GroupWallet.objects.all()
    serializer_class = GroupWalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def deposit(self, request, pk=None):
        amount = request.data.get('amount')
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError()
        except Exception:
            return Response({'detail': 'Invalid amount'}, status=400)
        wallet = self.get_object()
        wallet.balance = wallet.balance + amount
        wallet.save(update_fields=['balance'])
        return Response({'detail': 'Deposit successful', 'balance': wallet.balance}, status=200)

    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        amount = request.data.get('amount')
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError()
        except Exception:
            return Response({'detail': 'Invalid amount'}, status=400)
        wallet = self.get_object()
        if wallet.balance < amount:
            return Response({'detail': 'Insufficient balance'}, status=400)
        wallet.balance = wallet.balance - amount
        wallet.save(update_fields=['balance'])
        return Response({'detail': 'Withdrawal successful', 'balance': wallet.balance}, status=200)


