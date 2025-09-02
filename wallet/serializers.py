from rest_framework import serializers
from .models import Wallet, WalletTransaction

class WalletSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Wallet
        fields = ['id', 'owner', 'owner_username', 'balance', 'created_at', 'updated_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'wallet', 'transaction_type', 'amount', 'reference', 'created_at']
