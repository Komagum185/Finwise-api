from django.contrib import admin
from django.utils.html import format_html
from .models import Customer, CustomerFeedback, SMSCampaign


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'customer_type', 'total_spent', 'rating', 'status', 'created_at']
    list_filter = ['customer_type', 'status', 'created_at', 'last_purchase']
    search_fields = ['name', 'phone', 'email', 'location']
    readonly_fields = ['id', 'average_order_value', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'phone', 'email', 'location')
        }),
        ('Customer Details', {
            'fields': ('customer_type', 'status', 'notes')
        }),
        ('Financial Information', {
            'fields': ('total_purchases', 'total_spent', 'average_order_value', 'loyalty_points')
        }),
        ('Performance', {
            'fields': ('rating', 'last_purchase', 'favorite_products')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(CustomerFeedback)
class CustomerFeedbackAdmin(admin.ModelAdmin):
    list_display = ['customer', 'rating', 'product', 'date', 'created_at']
    list_filter = ['rating', 'date', 'created_at']
    search_fields = ['customer__name', 'comment', 'product']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Feedback Information', {
            'fields': ('customer', 'user', 'rating', 'comment', 'product', 'date')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'user')


@admin.register(SMSCampaign)
class SMSCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'total_recipients', 'success_rate', 'scheduled_date', 'created_at']
    list_filter = ['status', 'scheduled_date', 'created_at']
    search_fields = ['name', 'message']
    readonly_fields = ['id', 'total_recipients', 'success_rate', 'sent_date', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Campaign Information', {
            'fields': ('user', 'name', 'message', 'recipients')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'status')
        }),
        ('Delivery Statistics', {
            'fields': ('sent_date', 'success_count', 'failure_count', 'total_recipients', 'success_rate')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_recipients(self, obj):
        return obj.get_total_recipients()
    total_recipients.short_description = 'Total Recipients'
    
    def success_rate(self, obj):
        rate = obj.get_success_rate()
        color = 'green' if rate >= 80 else 'orange' if rate >= 60 else 'red'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, rate)
    success_rate.short_description = 'Success Rate'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    actions = ['mark_as_sent', 'mark_as_failed']
    
    def mark_as_sent(self, request, queryset):
        for campaign in queryset:
            if campaign.status == 'draft':
                campaign.mark_as_sent()
        self.message_user(request, f"Marked {queryset.count()} campaigns as sent.")
    mark_as_sent.short_description = "Mark selected campaigns as sent"
    
    def mark_as_failed(self, request, queryset):
        for campaign in queryset:
            if campaign.status in ['draft', 'scheduled']:
                campaign.mark_as_failed()
        self.message_user(request, f"Marked {queryset.count()} campaigns as failed.")
    mark_as_failed.short_description = "Mark selected campaigns as failed"
