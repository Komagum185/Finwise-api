from django.contrib import admin
from .models import LoanProduct, GroupLoan, GroupLoanRepayment


@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'loan_type', 'min_amount', 'max_amount', 
        'interest_rate', 'term_min', 'term_max', 'is_active'
    ]
    list_filter = [
        'loan_type', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']


@admin.register(GroupLoan)
class GroupLoanAdmin(admin.ModelAdmin):
    list_display = [
        'mse', 'amount', 'term_months', 'interest_rate', 
        'status', 'approval_date', 'created_at'
    ]
    list_filter = [
        'status', 'created_at', 'approval_date', 'disbursement_date'
    ]
    search_fields = [
        'mse__first_name', 'mse__last_name', 'mse__business_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Loan Information', {
            'fields': ('amount', 'term_months', 'interest_rate', 'purpose')
        }),
        ('MSE & Management', {
            'fields': ('mse', 'loan_product', 'assigned_agent')
        }),
        ('Status & Approval', {
            'fields': ('status', 'approval_date', 'approved_by')
        }),
        ('Disbursement', {
            'fields': ('disbursement_date', 'disbursement_amount')
        }),
        ('Financial Tracking', {
            'fields': ('total_interest', 'total_principal_paid', 'outstanding_balance')
        }),
        ('Additional Information', {
            'fields': ('collateral', 'guarantor_name', 'guarantor_phone')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GroupLoanRepayment)
class GroupLoanRepaymentAdmin(admin.ModelAdmin):
    list_display = [
        'loan', 'amount', 'repayment_type', 'is_confirmed', 'payment_date'
    ]
    list_filter = ['repayment_type', 'is_confirmed', 'payment_date']
    search_fields = ['loan__mse__first_name', 'loan__mse__last_name', 'reference_number']
    readonly_fields = ['created_at', 'payment_date']
    ordering = ['-payment_date']
