from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import KYCDocument, BankAccount, MobileMoneyAccount, KYCVerification, VerificationRequest


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'document_type', 'user_name', 'document_number', 'status', 'file_size_mb',
        'uploaded_at', 'verified_at'
    ]
    list_filter = ['document_type', 'status', 'uploaded_at', 'verified_at']
    search_fields = ['user__username', 'user__email', 'document_number', 'filename']
    readonly_fields = ['id', 'uploaded_at', 'updated_at', 'file_size', 'file_size_mb']
    fieldsets = (
        ('Document Information', {
            'fields': ('id', 'user', 'document_type', 'document_number', 'issuing_country')
        }),
        ('Dates', {
            'fields': ('issue_date', 'expiry_date')
        }),
        ('File Information', {
            'fields': ('file', 'filename', 'file_size', 'file_size_mb', 'file_type')
        }),
        ('Verification', {
            'fields': ('status', 'verified_by', 'verified_at', 'verification_notes')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_name.short_description = 'User'
    
    def file_size_mb(self, obj):
        return f"{obj.get_file_size_mb()} MB"
    file_size_mb.short_description = 'File Size'
    
    actions = ['approve_documents', 'reject_documents']
    
    def approve_documents(self, request, queryset):
        updated = 0
        for document in queryset:
            if document.status == 'pending':
                document.status = 'approved'
                document.verified_by = request.user
                document.save()
                updated += 1
        self.message_user(request, f'{updated} documents were approved.')
    approve_documents.short_description = "Approve selected documents"
    
    def reject_documents(self, request, queryset):
        updated = 0
        for document in queryset:
            if document.status == 'pending':
                document.status = 'rejected'
                document.verified_by = request.user
                document.save()
                updated += 1
        self.message_user(request, f'{updated} documents were rejected.')
    reject_documents.short_description = "Reject selected documents"


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = [
        'bank_name', 'user_name', 'account_number', 'account_type', 'status',
        'currency', 'created_at', 'verified_at'
    ]
    list_filter = ['account_type', 'status', 'currency', 'created_at', 'verified_at']
    search_fields = ['user__username', 'user__email', 'bank_name', 'account_number', 'account_holder_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Account Information', {
            'fields': ('id', 'user', 'bank_name', 'branch_name', 'account_number')
        }),
        ('Account Details', {
            'fields': ('account_type', 'account_holder_name', 'currency', 'is_active')
        }),
        ('Verification', {
            'fields': ('status', 'verified_by', 'verified_at', 'verification_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_name.short_description = 'User'
    
    actions = ['verify_accounts', 'reject_accounts']
    
    def verify_accounts(self, request, queryset):
        updated = 0
        for account in queryset:
            if account.status == 'pending':
                account.status = 'verified'
                account.verified_by = request.user
                account.save()
                updated += 1
        self.message_user(request, f'{updated} bank accounts were verified.')
    verify_accounts.short_description = "Verify selected bank accounts"
    
    def reject_accounts(self, request, queryset):
        updated = 0
        for account in queryset:
            if account.status == 'pending':
                account.status = 'rejected'
                account.verified_by = request.user
                account.save()
                updated += 1
        self.message_user(request, f'{updated} bank accounts were rejected.')
    reject_accounts.short_description = "Reject selected bank accounts"


@admin.register(MobileMoneyAccount)
class MobileMoneyAccountAdmin(admin.ModelAdmin):
    list_display = [
        'provider', 'user_name', 'phone_number', 'account_name', 'status',
        'created_at', 'verified_at'
    ]
    list_filter = ['provider', 'status', 'created_at', 'verified_at']
    search_fields = ['user__username', 'user__email', 'phone_number', 'account_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Account Information', {
            'fields': ('id', 'user', 'provider', 'phone_number', 'account_name', 'is_active')
        }),
        ('Verification', {
            'fields': ('status', 'verified_by', 'verified_at', 'verification_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_name.short_description = 'User'
    
    actions = ['verify_accounts', 'reject_accounts']
    
    def verify_accounts(self, request, queryset):
        updated = 0
        for account in queryset:
            if account.status == 'pending':
                account.status = 'verified'
                account.verified_by = request.user
                account.save()
                updated += 1
        self.message_user(request, f'{updated} mobile money accounts were verified.')
    verify_accounts.short_description = "Verify selected mobile money accounts"
    
    def reject_accounts(self, request, queryset):
        updated = 0
        for account in queryset:
            if account.status == 'pending':
                account.status = 'rejected'
                account.verified_by = request.user
                account.save()
                updated += 1
        self.message_user(request, f'{updated} mobile money accounts were rejected.')
    reject_accounts.short_description = "Reject selected mobile money accounts"


@admin.register(KYCVerification)
class KYCVerificationAdmin(admin.ModelAdmin):
    list_display = [
        'user_name', 'verification_level', 'status', 'verification_progress',
        'documents_verified', 'bank_accounts_verified', 'mobile_accounts_verified',
        'created_at', 'verified_at'
    ]
    list_filter = ['verification_level', 'status', 'created_at', 'verified_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'verification_progress', 'created_at', 'updated_at']
    fieldsets = (
        ('Verification Information', {
            'fields': ('id', 'user', 'verification_level', 'status')
        }),
        ('Progress Tracking', {
            'fields': ('documents_uploaded', 'documents_verified', 'bank_accounts_verified',
                      'mobile_accounts_verified', 'verification_progress')
        }),
        ('Requirements', {
            'fields': ('required_documents', 'required_bank_accounts', 'required_mobile_accounts')
        }),
        ('Verification Details', {
            'fields': ('verified_by', 'verified_at', 'verification_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_name.short_description = 'User'
    
    def verification_progress(self, obj):
        return f"{obj.get_verification_progress()}%"
    verification_progress.short_description = 'Progress'
    
    actions = ['approve_verifications', 'reject_verifications']
    
    def approve_verifications(self, request, queryset):
        updated = 0
        for verification in queryset:
            if verification.status == 'pending_review':
                verification.status = 'approved'
                verification.verified_by = request.user
                verification.save()
                updated += 1
        self.message_user(request, f'{updated} KYC verifications were approved.')
    approve_verifications.short_description = "Approve selected KYC verifications"
    
    def reject_verifications(self, request, queryset):
        updated = 0
        for verification in queryset:
            if verification.status == 'pending_review':
                verification.status = 'rejected'
                verification.verified_by = request.user
                verification.save()
                updated += 1
        self.message_user(request, f'{updated} KYC verifications were rejected.')
    reject_verifications.short_description = "Reject selected KYC verifications"


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_type', 'user_name', 'title', 'status', 'priority', 'created_at',
        'reviewed_at'
    ]
    list_filter = ['request_type', 'status', 'priority', 'created_at', 'reviewed_at']
    search_fields = ['user__username', 'user__email', 'title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Request Information', {
            'fields': ('id', 'user', 'request_type', 'title', 'description', 'priority')
        }),
        ('Related Objects', {
            'fields': ('document', 'bank_account', 'mobile_account', 'kyc_verification')
        }),
        ('Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_name.short_description = 'User'
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        updated = 0
        for req in queryset:
            if req.status == 'pending':
                req.status = 'approved'
                req.reviewed_by = request.user
                req.save()
                updated += 1
        self.message_user(request, f'{updated} verification requests were approved.')
    approve_requests.short_description = "Approve selected verification requests"
    
    def reject_requests(self, request, queryset):
        updated = 0
        for req in queryset:
            if req.status == 'pending':
                req.status = 'rejected'
                req.reviewed_by = request.user
                req.save()
                updated += 1
        self.message_user(request, f'{updated} verification requests were rejected.')
    reject_requests.short_description = "Reject selected verification requests"
