from django.contrib import admin
from .models import Wallet, WalletTransaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        'owner', 'balance', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['owner__first_name', 'owner__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'wallet', 'transaction_type', 'amount', 'status', 'created_at'
    ]
    list_filter = [
        'transaction_type', 'status', 'created_at'
    ]
    search_fields = [
        'wallet__owner__first_name', 'wallet__owner__last_name',
        'reference_number', 'description'
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_type', 'amount', 'status')
        }),
        ('Wallet & Balance', {
            'fields': ('wallet', 'balance_before', 'balance_after')
        }),
        ('Related Entities', {
            'fields': ('related_loan', 'related_transaction')
        }),
        ('Additional Information', {
            'fields': ('reference_number', 'description', 'metadata')
        }),
        ('Processing', {
            'fields': ('processed_by', 'processed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
