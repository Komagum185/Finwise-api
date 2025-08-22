from django.contrib import admin
from .models import USSDUser, Wallet, Transaction, Product, Loan, Contact, USSDSession, WalletAuditLog


@admin.register(USSDUser)
class USSDUserAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'is_active', 'ussd_enabled', 'created_at']
    list_filter = ['is_active', 'ussd_enabled', 'created_at']
    search_fields = ['name', 'phone']
    readonly_fields = ['created_at']


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['owner', 'balance', 'created_at']
    list_filter = ['created_at']
    search_fields = ['owner__name', 'owner__phone']
    readonly_fields = ['created_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'type', 'amount', 'status', 'created_at']
    list_filter = ['type', 'status', 'created_at']
    search_fields = ['wallet__owner__name', 'wallet__owner__phone', 'reference']
    readonly_fields = ['created_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'price', 'stock', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'owner__name']
    readonly_fields = ['created_at']


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['borrower', 'amount_requested', 'amount_approved', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['borrower__name', 'borrower__phone']
    readonly_fields = ['created_at']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'phone', 'relationship_type']
    list_filter = ['relationship_type']
    search_fields = ['name', 'owner__name', 'phone']
    readonly_fields = ['created_at']


@admin.register(USSDSession)
class USSDSessionAdmin(admin.ModelAdmin):
    list_display = ['msisdn', 'session_id', 'current_step', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'current_step', 'created_at']
    search_fields = ['msisdn', 'session_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WalletAuditLog)
class WalletAuditLogAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'action', 'amount', 'balance_before', 'balance_after', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['wallet__owner__name', 'wallet__owner__phone', 'reference']
    readonly_fields = ['created_at']
