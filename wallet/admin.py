from django.contrib import admin
from .models import (
    Category, Transaction, Budget, Goal, 
    EnhancedWallet, EnhancedWalletTransaction, 
    WalletTransfer, WalletStatistics
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'is_active', 'created_at']
    list_filter = ['category_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(EnhancedWallet)
class EnhancedWalletAdmin(admin.ModelAdmin):
    list_display = [
        'mse_name', 'mse_code', 'account_number', 'account_type', 
        'balance', 'currency', 'status', 'transaction_count', 'monthly_volume'
    ]
    list_filter = ['account_type', 'status', 'currency', 'created_at']
    search_fields = ['mse_name', 'mse_code', 'account_number', 'mse_id']
    readonly_fields = ['transaction_count', 'monthly_volume', 'last_transaction']
    ordering = ['-created_at']
    
    fieldsets = (
        ('MSE Information', {
            'fields': ('mse_id', 'mse_name', 'mse_code')
        }),
        ('Account Details', {
            'fields': ('account_number', 'account_type', 'description')
        }),
        ('Financial Information', {
            'fields': ('balance', 'currency', 'status')
        }),
        ('Statistics', {
            'fields': ('transaction_count', 'monthly_volume', 'last_transaction'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(EnhancedWalletTransaction)
class EnhancedWalletTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'wallet', 'type', 'amount', 'currency', 'status', 
        'category', 'date', 'reference'
    ]
    list_filter = ['type', 'status', 'category', 'date', 'created_at']
    search_fields = ['description', 'reference', 'wallet__mse_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-date']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('wallet', 'type', 'amount', 'description', 'date', 'status')
        }),
        ('Additional Information', {
            'fields': ('reference', 'category', 'related_transaction_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def currency(self, obj):
        return obj.wallet.currency
    currency.short_description = 'Currency'


@admin.register(WalletTransfer)
class WalletTransferAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'from_wallet', 'to_wallet', 'amount', 'currency', 
        'status', 'created_at'
    ]
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['description', 'from_wallet__mse_name', 'to_wallet__mse_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transfer Details', {
            'fields': ('from_wallet', 'to_wallet', 'amount', 'currency', 'description', 'status')
        }),
        ('Transaction References', {
            'fields': ('debit_transaction', 'credit_transaction'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(WalletStatistics)
class WalletStatisticsAdmin(admin.ModelAdmin):
    list_display = [
        'wallet', 'total_balance', 'total_wallets', 'active_wallets',
        'monthly_volume', 'monthly_transactions', 'currency', 'last_updated'
    ]
    list_filter = ['currency', 'last_updated']
    readonly_fields = ['last_updated']
    ordering = ['-last_updated']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'amount', 'currency', 'transaction_type', 
        'status', 'transaction_date', 'wallet'
    ]
    list_filter = ['transaction_type', 'status', 'currency', 'transaction_date', 'created_at']
    search_fields = ['title', 'description', 'reference_number', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-transaction_date']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'budget_type', 'total_amount', 'spent_amount', 
        'remaining_amount', 'status', 'start_date', 'end_date'
    ]
    list_filter = ['budget_type', 'status', 'start_date', 'end_date', 'created_at']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['remaining_amount', 'created_at', 'updated_at']
    ordering = ['-start_date']


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'goal_type', 'target_amount', 'current_amount', 
        'progress_percentage', 'status', 'target_date'
    ]
    list_filter = ['goal_type', 'status', 'target_date', 'created_at']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['remaining_amount', 'progress_percentage', 'created_at', 'updated_at']
    ordering = ['-target_date']

