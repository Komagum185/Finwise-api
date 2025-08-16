from django.contrib import admin
from .models import (
    Category, Transaction, Budget, Goal, 
    EnhancedWallet, EnhancedWalletTransaction, 
    WalletTransfer, WalletStatistics,
    PaymentTransaction, BulkPayment, BulkPaymentRecipient
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


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'transaction_type', 'provider', 'phone_number', 
        'amount', 'total_amount', 'status', 'timestamp'
    ]
    list_filter = ['transaction_type', 'provider', 'status', 'timestamp']
    search_fields = ['phone_number', 'reference', 'description', 'user__username']
    readonly_fields = ['id', 'total_amount', 'timestamp']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('user', 'transaction_type', 'provider', 'phone_number')
        }),
        ('Financial Details', {
            'fields': ('amount', 'fee', 'total_amount', 'reference')
        }),
        ('Status & Confirmation', {
            'fields': ('status', 'description', 'confirmation_code')
        }),
        ('Timestamps', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_failed', 'mark_as_cancelled']
    
    def mark_as_completed(self, request, queryset):
        for transaction in queryset:
            if transaction.status in ['pending', 'processing']:
                transaction.status = 'completed'
                transaction.save()
        self.message_user(request, f"Marked {queryset.count()} transactions as completed.")
    mark_as_completed.short_description = "Mark selected transactions as completed"
    
    def mark_as_failed(self, request, queryset):
        for transaction in queryset:
            if transaction.status in ['pending', 'processing']:
                transaction.status = 'failed'
                transaction.save()
        self.message_user(request, f"Marked {queryset.count()} transactions as failed.")
    mark_as_failed.short_description = "Mark selected transactions as failed"
    
    def mark_as_cancelled(self, request, queryset):
        for transaction in queryset:
            if transaction.status in ['pending', 'processing']:
                transaction.status = 'cancelled'
                transaction.save()
        self.message_user(request, f"Marked {queryset.count()} transactions as cancelled.")
    mark_as_cancelled.short_description = "Mark selected transactions as cancelled"


@admin.register(BulkPayment)
class BulkPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'total_amount', 'recipient_count', 'status', 
        'scheduled_date', 'created_at'
    ]
    list_filter = ['status', 'scheduled_date', 'created_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Bulk Payment Information', {
            'fields': ('user', 'name', 'total_amount', 'recipient_count')
        }),
        ('Scheduling', {
            'fields': ('status', 'scheduled_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_processing', 'mark_as_completed', 'mark_as_failed']
    
    def mark_as_processing(self, request, queryset):
        for bulk_payment in queryset:
            if bulk_payment.status in ['draft', 'scheduled']:
                bulk_payment.mark_as_processing()
        self.message_user(request, f"Marked {queryset.count()} bulk payments as processing.")
    mark_as_processing.short_description = "Mark selected bulk payments as processing"
    
    def mark_as_completed(self, request, queryset):
        for bulk_payment in queryset:
            if bulk_payment.status == 'processing':
                bulk_payment.mark_as_completed()
        self.message_user(request, f"Marked {queryset.count()} bulk payments as completed.")
    mark_as_completed.short_description = "Mark selected bulk payments as completed"
    
    def mark_as_failed(self, request, queryset):
        for bulk_payment in queryset:
            if bulk_payment.status == 'processing':
                bulk_payment.mark_as_failed()
        self.message_user(request, f"Marked {queryset.count()} bulk payments as failed.")
    mark_as_failed.short_description = "Mark selected bulk payments as failed"


@admin.register(BulkPaymentRecipient)
class BulkPaymentRecipientAdmin(admin.ModelAdmin):
    list_display = [
        'bulk_payment', 'phone_number', 'name', 'amount', 'status', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['phone_number', 'name', 'bulk_payment__name']
    readonly_fields = ['id', 'created_at']
    ordering = ['created_at']
    
    fieldsets = (
        ('Recipient Information', {
            'fields': ('bulk_payment', 'phone_number', 'name', 'amount')
        }),
        ('Status & Reference', {
            'fields': ('status', 'reference')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_sent', 'mark_as_failed']
    
    def mark_as_sent(self, request, queryset):
        for recipient in queryset:
            if recipient.status == 'pending':
                recipient.mark_as_sent()
        self.message_user(request, f"Marked {queryset.count()} recipients as sent.")
    mark_as_sent.short_description = "Mark selected recipients as sent"
    
    def mark_as_failed(self, request, queryset):
        for recipient in queryset:
            if recipient.status == 'pending':
                recipient.mark_as_failed()
        self.message_user(request, f"Marked {queryset.count()} recipients as failed.")
    mark_as_failed.short_description = "Mark selected recipients as failed"

