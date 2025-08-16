from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import LoanApplication, Loan, LoanSchedule, LoanPayment, LoanDocument


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'applicant_name', 'mse_name', 'requested_amount', 'status', 
        'risk_level', 'created_at', 'submitted_at'
    ]
    list_filter = ['status', 'risk_level', 'created_at', 'submitted_at']
    search_fields = ['applicant__username', 'applicant__email', 'mse__name', 'purpose']
    readonly_fields = ['id', 'created_at', 'updated_at', 'submitted_at', 'reviewed_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'applicant', 'mse', 'requested_amount', 'purpose')
        }),
        ('Business Details', {
            'fields': ('business_plan', 'collateral_description')
        }),
        ('Application Status', {
            'fields': ('status', 'submitted_at', 'reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('Risk Assessment', {
            'fields': ('credit_score', 'risk_level')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def applicant_name(self, obj):
        return obj.applicant.get_full_name() or obj.applicant.username
    applicant_name.short_description = 'Applicant'
    
    def mse_name(self, obj):
        return obj.mse.name
    mse_name.short_description = 'MSE'
    
    actions = ['approve_applications', 'reject_applications']
    
    def approve_applications(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} applications were approved.')
    approve_applications.short_description = "Approve selected applications"
    
    def reject_applications(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} applications were rejected.')
    reject_applications.short_description = "Reject selected applications"


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'mse_name', 'loan_type', 'principal_amount', 'interest_rate', 
        'term_months', 'status', 'outstanding_balance', 'disbursed_at'
    ]
    list_filter = ['status', 'loan_type', 'payment_frequency', 'disbursed_at', 'created_at']
    search_fields = ['mse__name', 'application__applicant__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_interest', 'total_paid', 'outstanding_balance']
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'application', 'mse', 'loan_type')
        }),
        ('Loan Terms', {
            'fields': ('principal_amount', 'interest_rate', 'term_months', 'payment_frequency')
        }),
        ('Status & Dates', {
            'fields': ('status', 'disbursed_at', 'maturity_date')
        }),
        ('Financial Tracking', {
            'fields': ('total_interest', 'total_paid', 'outstanding_balance', 'days_past_due', 'late_fees_charged')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def mse_name(self, obj):
        return obj.mse.name
    mse_name.short_description = 'MSE'
    
    actions = ['disburse_loans', 'mark_as_paid_off']
    
    def disburse_loans(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for loan in queryset:
            if loan.status == 'active' and not loan.disbursed_at:
                loan.disbursed_at = timezone.now()
                loan.save()
                updated += 1
        self.message_user(request, f'{updated} loans were disbursed.')
    disburse_loans.short_description = "Disburse selected loans"
    
    def mark_as_paid_off(self, request, queryset):
        updated = queryset.update(status='paid_off')
        self.message_user(request, f'{updated} loans were marked as paid off.')
    mark_as_paid_off.short_description = "Mark selected loans as paid off"


@admin.register(LoanSchedule)
class LoanScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'payment_number', 'loan_id', 'due_date', 'total_due', 'amount_paid', 
        'status', 'days_overdue', 'late_fees'
    ]
    list_filter = ['status', 'due_date', 'loan__status']
    search_fields = ['loan__mse__name', 'loan__id']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Payment Information', {
            'fields': ('loan', 'payment_number', 'due_date')
        }),
        ('Amounts', {
            'fields': ('principal_due', 'interest_due', 'total_due', 'balance_after_payment')
        }),
        ('Payment Status', {
            'fields': ('amount_paid', 'payment_date', 'status')
        }),
        ('Late Payment', {
            'fields': ('days_overdue', 'late_fees')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def loan_id(self, obj):
        return str(obj.loan.id)[:8]
    loan_id.short_description = 'Loan ID'


@admin.register(LoanPayment)
class LoanPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'loan_id', 'schedule_number', 'amount', 'payment_method', 
        'payment_date', 'reference'
    ]
    list_filter = ['payment_method', 'payment_date', 'loan__status']
    search_fields = ['loan__mse__name', 'reference', 'notes']
    readonly_fields = ['payment_date', 'created_at', 'updated_at']
    fieldsets = (
        ('Payment Information', {
            'fields': ('loan', 'schedule', 'amount', 'payment_method')
        }),
        ('Details', {
            'fields': ('reference', 'notes', 'wallet_transaction')
        }),
        ('Timestamps', {
            'fields': ('payment_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def loan_id(self, obj):
        return str(obj.loan.id)[:8]
    loan_id.short_description = 'Loan ID'
    
    def schedule_number(self, obj):
        return obj.schedule.payment_number
    schedule_number.short_description = 'Payment #'


@admin.register(LoanDocument)
class LoanDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'filename', 'document_type', 'uploaded_by_name', 'uploaded_at', 
        'file_size_mb', 'loan_application', 'loan'
    ]
    list_filter = ['document_type', 'uploaded_at', 'loan_application__status', 'loan__status']
    search_fields = ['filename', 'uploaded_by__username', 'uploaded_by__email']
    readonly_fields = ['uploaded_at', 'file_size']
    fieldsets = (
        ('Document Information', {
            'fields': ('document_type', 'file', 'filename', 'file_size')
        }),
        ('Related Records', {
            'fields': ('loan_application', 'loan')
        }),
        ('Upload Information', {
            'fields': ('uploaded_by', 'uploaded_at')
        })
    )
    
    def uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
    uploaded_by_name.short_description = 'Uploaded By'
    
    def file_size_mb(self, obj):
        return f"{obj.file_size / (1024 * 1024):.2f} MB"
    file_size_mb.short_description = 'File Size'
