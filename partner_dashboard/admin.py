from django.contrib import admin
from .models import Beneficiary, DigitalServiceUsage, PartnerDashboard


@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = [
        'first_name', 'last_name', 'gender', 'age_group', 'region', 
        'district', 'mse', 'is_refugee', 'has_disability'
    ]
    list_filter = [
        'gender', 'age_group', 'is_refugee', 'has_disability', 
        'region', 'district', 'created_at'
    ]
    search_fields = ['first_name', 'last_name', 'mse__first_name', 'mse__last_name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'gender', 'age_group')
        }),
        ('Demographics', {
            'fields': ('is_refugee', 'has_disability')
        }),
        ('Location', {
            'fields': ('region', 'district', 'subcounty')
        }),
        ('Contact', {
            'fields': ('contact_number',)
        }),
        ('MSE Association', {
            'fields': ('mse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(DigitalServiceUsage)
class DigitalServiceUsageAdmin(admin.ModelAdmin):
    list_display = [
        'mse', 'service_type', 'service_name', 'region', 
        'district', 'beneficiaries_count', 'usage_frequency'
    ]
    list_filter = [
        'service_type', 'usage_frequency', 'region', 'district', 'created_at'
    ]
    search_fields = [
        'mse__first_name', 'mse__last_name', 'service_name', 'region', 'district'
    ]
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Service Information', {
            'fields': ('service_type', 'service_name', 'usage_frequency')
        }),
        ('MSE Details', {
            'fields': ('mse', 'beneficiaries_count')
        }),
        ('Location', {
            'fields': ('region', 'district')
        }),
        ('Contact', {
            'fields': ('contact_number',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(PartnerDashboard)
class PartnerDashboardAdmin(admin.ModelAdmin):
    list_display = [
        'partner', 'last_access', 'access_count', 'created_at'
    ]
    list_filter = ['last_access', 'created_at']
    search_fields = ['partner__username', 'partner__first_name', 'partner__last_name']
    readonly_fields = ['last_access', 'access_count', 'created_at']
    ordering = ['-last_access']
    
    fieldsets = (
        ('Partner Information', {
            'fields': ('partner',)
        }),
        ('Access Statistics', {
            'fields': ('access_count', 'last_access')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Partner dashboard records are created automatically
        return False
