from django.contrib import admin
from .models import PaymentProvider, QRPayment, ScheduledTransfer, PaymentTransaction


@admin.register(PaymentProvider)
class PaymentProviderAdmin(admin.ModelAdmin):
    """Admin interface for PaymentProvider"""
    list_display = ['name', 'provider_id', 'type', 'country', 'currency', 'status', 'created_at']
    list_filter = ['type', 'country', 'currency', 'status', 'created_at']
    search_fields = ['name', 'provider_id', 'country']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'provider_id', 'type', 'country', 'currency')
        }),
        ('Fee Structure', {
            'fields': ('fee_percentage', 'fee_fixed', 'min_amount', 'max_amount')
        }),
        ('Configuration', {
            'fields': ('api_key', 'api_secret', 'webhook_url', 'status'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['activate_providers', 'deactivate_providers']
    
    def activate_providers(self, request, queryset):
        """Activate selected providers"""
        updated = queryset.update(status='active')
        self.message_user(request, f'Successfully activated {updated} providers.')
    activate_providers.short_description = "Activate selected providers"
    
    def deactivate_providers(self, request, queryset):
        """Deactivate selected providers"""
        updated = queryset.update(status='inactive')
        self.message_user(request, f'Successfully deactivated {updated} providers.')
    deactivate_providers.short_description = "Deactivate selected providers"


@admin.register(QRPayment)
class QRPaymentAdmin(admin.ModelAdmin):
    """Admin interface for QRPayment"""
    list_display = ['id', 'user', 'amount', 'currency', 'status', 'created_at', 'expires_at', 'is_expired_display']
    list_filter = ['status', 'currency', 'created_at', 'expires_at']
    search_fields = ['user__username', 'user__email', 'description', 'transaction_id']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('user', 'amount', 'currency', 'description', 'provider')
        }),
        ('QR Code', {
            'fields': ('qr_code', 'qr_url'),
            'classes': ('collapse',)
        }),
        ('Status & Timing', {
            'fields': ('status', 'created_at', 'expires_at', 'completed_at')
        }),
        ('Payment Details', {
            'fields': ('transaction_id', 'payer_phone', 'payer_name'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['id', 'user', 'qr_code', 'qr_url', 'created_at', 'expires_at', 'completed_at']
    
    def is_expired_display(self, obj):
        """Display if QR payment is expired"""
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = 'Expired'
    
    actions = ['mark_completed', 'mark_expired', 'mark_cancelled']
    
    def mark_completed(self, request, queryset):
        """Mark selected QR payments as completed"""
        for qr_payment in queryset:
            if qr_payment.status == 'pending' and not qr_payment.is_expired():
                qr_payment.mark_completed()
        self.message_user(request, f'Successfully marked QR payments as completed.')
    mark_completed.short_description = "Mark as completed"
    
    def mark_expired(self, request, queryset):
        """Mark selected QR payments as expired"""
        updated = queryset.filter(status='pending').update(status='expired')
        self.message_user(request, f'Successfully marked {updated} QR payments as expired.')
    mark_expired.short_description = "Mark as expired"
    
    def mark_cancelled(self, request, queryset):
        """Mark selected QR payments as cancelled"""
        updated = queryset.filter(status='pending').update(status='cancelled')
        self.message_user(request, f'Successfully marked {updated} QR payments as cancelled.')
    mark_cancelled.short_description = "Mark as cancelled"


@admin.register(ScheduledTransfer)
class ScheduledTransferAdmin(admin.ModelAdmin):
    """Admin interface for ScheduledTransfer"""
    list_display = ['id', 'user', 'amount', 'currency', 'frequency', 'status', 'next_execution', 'is_due_display']
    list_filter = ['frequency', 'status', 'currency', 'created_at']
    search_fields = ['user__username', 'user__email', 'description', 'from_wallet', 'to_wallet', 'phone_number']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transfer Information', {
            'fields': ('user', 'amount', 'currency', 'description', 'provider')
        }),
        ('Transfer Details', {
            'fields': ('from_wallet', 'to_wallet', 'phone_number')
        }),
        ('Scheduling', {
            'fields': ('frequency', 'next_execution', 'last_execution')
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'updated_at')
        })
    )
    
    readonly_fields = ['id', 'user', 'last_execution', 'created_at', 'updated_at']
    
    def is_due_display(self, obj):
        """Display if transfer is due"""
        return obj.is_due()
    is_due_display.boolean = True
    is_due_display.short_description = 'Due'
    
    actions = ['pause_transfers', 'resume_transfers', 'cancel_transfers']
    
    def pause_transfers(self, request, queryset):
        """Pause selected transfers"""
        updated = queryset.filter(status='active').update(status='paused')
        self.message_user(request, f'Successfully paused {updated} transfers.')
    pause_transfers.short_description = "Pause transfers"
    
    def resume_transfers(self, request, queryset):
        """Resume selected transfers"""
        updated = queryset.filter(status='paused').update(status='active')
        self.message_user(request, f'Successfully resumed {updated} transfers.')
    resume_transfers.short_description = "Resume transfers"
    
    def cancel_transfers(self, request, queryset):
        """Cancel selected transfers"""
        updated = queryset.filter(status__in=['active', 'paused']).update(status='cancelled')
        self.message_user(request, f'Successfully cancelled {updated} transfers.')
    cancel_transfers.short_description = "Cancel transfers"


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    """Admin interface for PaymentTransaction"""
    list_display = ['reference', 'user', 'type', 'amount', 'currency', 'status', 'created_at', 'processed_at']
    list_filter = ['type', 'status', 'currency', 'created_at']
    search_fields = ['reference', 'user__username', 'user__email', 'description', 'external_transaction_id']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('user', 'type', 'amount', 'currency', 'description')
        }),
        ('Financial Details', {
            'fields': ('fees', 'net_amount', 'provider')
        }),
        ('Reference & Status', {
            'fields': ('reference', 'external_transaction_id', 'status')
        }),
        ('Timing', {
            'fields': ('created_at', 'processed_at')
        }),
        ('Related Objects', {
            'fields': ('qr_payment', 'scheduled_transfer'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = [
        'reference', 'external_transaction_id', 'fees', 'net_amount', 
        'created_at', 'processed_at', 'metadata'
    ]
    
    actions = ['mark_completed', 'mark_failed', 'mark_cancelled']
    
    def mark_completed(self, request, queryset):
        """Mark selected transactions as completed"""
        for transaction in queryset:
            if transaction.status in ['pending', 'processing']:
                transaction.mark_completed()
        self.message_user(request, f'Successfully marked transactions as completed.')
    mark_completed.short_description = "Mark as completed"
    
    def mark_failed(self, request, queryset):
        """Mark selected transactions as failed"""
        updated = queryset.filter(status__in=['pending', 'processing']).update(status='failed')
        self.message_user(request, f'Successfully marked {updated} transactions as failed.')
    mark_failed.short_description = "Mark as failed"
    
    def mark_cancelled(self, request, queryset):
        """Mark selected transactions as cancelled"""
        updated = queryset.filter(status__in=['pending', 'processing']).update(status='cancelled')
        self.message_user(request, f'Successfully marked {updated} transactions as cancelled.')
    mark_cancelled.short_description = "Mark as cancelled"
