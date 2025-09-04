from django.contrib import admin
from .models import MSE, MSECategory, Wallet


@admin.register(MSECategory)
class MSECategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'description', 'created_at'
    ]
    list_filter = ['name', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    ordering = ['name']


@admin.register(MSE)
class MSEAdmin(admin.ModelAdmin):
    list_display = [
        'first_name', 'last_name', 'business_name', 'category', 
        'status', 'location', 'created_at'
    ]
    list_filter = [
        'status', 'category', 'created_at', 'approval_date'
    ]
    search_fields = [
        'first_name', 'last_name', 'business_name', 'nin', 
        'phone', 'email', 'location'
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'nin', 'phone', 'email', 'profile_image')
        }),
        ('Business Information', {
            'fields': ('business_name', 'business_type', 'registration_number', 'category')
        }),
        ('Location & Status', {
            'fields': ('location', 'status', 'approval_date', 'approved_by')
        }),
        ('Financial Information', {
            'fields': ('annual_revenue', 'employee_count')
        }),
        ('Management', {
            'fields': ('owner', 'assigned_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'owner', 'assigned_agent', 'approved_by')


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        'mse', 'balance', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['mse__first_name', 'mse__last_name', 'mse__business_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
