from rest_framework import serializers
from django.db.models import Sum, Count
from django.utils import timezone
from .models import (
    Category, Transaction, Budget, Goal, EnhancedWallet, 
    EnhancedWalletTransaction, WalletTransfer, WalletStatistics
)
from mses.models import Wallet as MSEWallet, WalletTransaction as MSEWalletTransaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


# Enhanced Wallet Serializers matching TypeScript interfaces
class EnhancedWalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for WalletTransaction matching TypeScript interface"""
    id = serializers.IntegerField(read_only=True)
    type = serializers.ChoiceField(choices=EnhancedWalletTransaction.TRANSACTION_TYPES)
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    description = serializers.CharField()
    date = serializers.DateTimeField(read_only=True)
    status = serializers.ChoiceField(choices=EnhancedWalletTransaction.STATUS_CHOICES)
    reference = serializers.CharField(required=False, allow_blank=True)
    category = serializers.ChoiceField(choices=EnhancedWalletTransaction.CATEGORY_CHOICES, required=False, allow_blank=True)
    related_transaction_id = serializers.PrimaryKeyRelatedField(
        queryset=EnhancedWalletTransaction.objects.all(), 
        required=False, 
        allow_null=True
    )
    
    class Meta:
        model = EnhancedWalletTransaction
        fields = [
            'id', 'type', 'amount', 'description', 'date', 'status',
            'reference', 'category', 'related_transaction_id'
        ]


class EnhancedWalletSerializer(serializers.ModelSerializer):
    """Serializer for Wallet matching TypeScript interface"""
    id = serializers.CharField(read_only=True)
    mse_id = serializers.CharField()
    mse_name = serializers.CharField()
    mse_code = serializers.CharField()
    account_number = serializers.CharField()
    account_type = serializers.ChoiceField(choices=EnhancedWallet.ACCOUNT_TYPES)
    balance = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    currency = serializers.CharField()
    status = serializers.ChoiceField(choices=EnhancedWallet.STATUS_CHOICES)
    last_transaction = serializers.DateTimeField(read_only=True)
    description = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    transaction_count = serializers.IntegerField(read_only=True)
    monthly_volume = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    
    class Meta:
        model = EnhancedWallet
        fields = [
            'id', 'mse_id', 'mse_name', 'mse_code', 'account_number', 'account_type',
            'balance', 'currency', 'status', 'last_transaction', 'description',
            'created_at', 'updated_at', 'transaction_count', 'monthly_volume'
        ]


class WalletTransferSerializer(serializers.ModelSerializer):
    """Serializer for WalletTransfer matching TypeScript interface"""
    from_wallet_id = serializers.CharField(source='from_wallet.id', read_only=True)
    to_wallet_id = serializers.CharField(source='to_wallet.id', read_only=True)
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    description = serializers.CharField()
    currency = serializers.CharField()
    
    class Meta:
        model = WalletTransfer
        fields = ['from_wallet_id', 'to_wallet_id', 'amount', 'description', 'currency']


class WalletTransactionRequestSerializer(serializers.Serializer):
    """Serializer for WalletTransactionRequest matching TypeScript interface"""
    wallet_id = serializers.CharField()
    type = serializers.ChoiceField(choices=EnhancedWalletTransaction.TRANSACTION_TYPES)
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    description = serializers.CharField()
    category = serializers.ChoiceField(choices=EnhancedWalletTransaction.CATEGORY_CHOICES, required=False, allow_blank=True)
    reference = serializers.CharField(required=False, allow_blank=True)


class WalletStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for WalletStatistics matching TypeScript interface"""
    total_balance = serializers.DecimalField(max_digits=20, decimal_places=2)
    total_wallets = serializers.IntegerField()
    active_wallets = serializers.IntegerField()
    monthly_volume = serializers.DecimalField(max_digits=20, decimal_places=2)
    monthly_transactions = serializers.IntegerField()
    currency = serializers.CharField()
    
    class Meta:
        model = WalletStatistics
        fields = [
            'total_balance', 'total_wallets', 'active_wallets',
            'monthly_volume', 'monthly_transactions', 'currency'
        ]


class WalletFilterSerializer(serializers.Serializer):
    """Serializer for WalletFilter matching TypeScript interface"""
    status = serializers.ChoiceField(choices=EnhancedWallet.STATUS_CHOICES, required=False)
    account_type = serializers.ChoiceField(choices=EnhancedWallet.ACCOUNT_TYPES, required=False)
    currency = serializers.CharField(required=False)
    date_range = serializers.DictField(required=False, child=serializers.CharField())


# Legacy serializers for backward compatibility
class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = MSEWallet
        fields = '__all__'


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MSEWalletTransaction
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    wallet_name = serializers.CharField(source='wallet.mse_name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class BudgetSerializer(serializers.ModelSerializer):
    spending_percentage = serializers.SerializerMethodField()
    is_over_budget = serializers.SerializerMethodField()
    
    class Meta:
        model = Budget
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'remaining_amount']
    
    def get_spending_percentage(self, obj):
        return obj.get_spending_percentage()
    
    def get_is_over_budget(self, obj):
        return obj.is_over_budget()


class GoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    
    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'remaining_amount', 'progress_percentage']
    
    def get_progress_percentage(self, obj):
        return obj.progress_percentage
    
    def get_days_remaining(self, obj):
        return obj.get_days_remaining()
    
    def get_is_completed(self, obj):
        return obj.is_completed()


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['title', 'description', 'amount', 'currency', 'transaction_type', 
                 'category', 'transaction_date', 'reference_number', 'tags', 
                 'wallet', 'location', 'notes']


class BudgetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['name', 'description', 'budget_type', 'total_amount', 
                 'start_date', 'end_date', 'category_limits', 'alert_threshold', 
                 'notifications_enabled']


class GoalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ['name', 'description', 'goal_type', 'target_amount', 
                 'target_date', 'monthly_target', 'motivation_note', 
                 'image_url', 'reminders_enabled', 'reminder_frequency']

