from django.contrib import admin
from .models import MSE, InputMSE, OutputMSE, ProductionMSE, MSECategory, Wallet, UserRole


@admin.register(MSE)
class MSEAdmin(admin.ModelAdmin):
    list_display = ['name', 'mse_type', 'status', 'user', 'business_type', 'created_at']
    list_filter = ['mse_type', 'status', 'business_type', 'created_at']
    search_fields = ['name', 'registration_number', 'tax_id', 'email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'mse_type', 'status', 'business_type', 'description')
        }),
        ('Registration Details', {
            'fields': ('registration_number', 'tax_id')
        }),
        ('Contact Information', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InputMSE)
class InputMSEAdmin(admin.ModelAdmin):
    list_display = ['mse', 'supplier_network_size', 'average_order_value', 'lead_time_days', 'created_at']
    list_filter = ['created_at']
    search_fields = ['mse__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('MSE Information', {
            'fields': ('mse',)
        }),
        ('Input Categories', {
            'fields': ('input_categories', 'primary_inputs', 'seasonal_inputs')
        }),
        ('Supplier Network', {
            'fields': ('supplier_network_size', 'average_order_value', 'lead_time_days')
        }),
        ('Quality & Storage', {
            'fields': ('quality_standards', 'storage_capacity', 'input_costs_tracking')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OutputMSE)
class OutputMSEAdmin(admin.ModelAdmin):
    list_display = ['mse', 'customer_network_size', 'average_sale_value', 'pricing_strategy', 'created_at']
    list_filter = ['created_at']
    search_fields = ['mse__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('MSE Information', {
            'fields': ('mse',)
        }),
        ('Output Categories', {
            'fields': ('output_categories', 'primary_products', 'seasonal_products')
        }),
        ('Customer Network', {
            'fields': ('customer_network_size', 'average_sale_value')
        }),
        ('Sales & Marketing', {
            'fields': ('sales_channels', 'marketing_strategy', 'pricing_strategy', 'delivery_methods')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductionMSE)
class ProductionMSEAdmin(admin.ModelAdmin):
    list_display = ['mse', 'production_capacity', 'daily_production_target', 'created_at']
    list_filter = ['created_at']
    search_fields = ['mse__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('MSE Information', {
            'fields': ('mse',)
        }),
        ('Production Details', {
            'fields': ('production_capacity', 'production_process', 'production_cycle_time')
        }),
        ('Equipment & Materials', {
            'fields': ('equipment_list', 'raw_materials_required')
        }),
        ('Quality & Safety', {
            'fields': ('quality_control', 'waste_management', 'safety_protocols')
        }),
        ('Capacity & Efficiency', {
            'fields': ('daily_production_target', 'efficiency_metrics', 'maintenance_schedule')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MSECategory)
class MSECategoryAdmin(admin.ModelAdmin):
    list_display = ['mse', 'primary_category', 'category_performance_score', 'category_growth_rate', 'created_at']
    list_filter = ['primary_category', 'created_at']
    search_fields = ['mse__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('MSE Information', {
            'fields': ('mse',)
        }),
        ('Category Classification', {
            'fields': ('primary_category', 'secondary_categories', 'category_description')
        }),
        ('Performance Metrics', {
            'fields': ('category_performance_score', 'category_growth_rate')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['name', 'mse', 'wallet_type', 'balance', 'currency', 'is_active']
    list_filter = ['wallet_type', 'currency', 'is_active', 'created_at']
    search_fields = ['name', 'mse__name', 'account_number']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Wallet Information', {
            'fields': ('mse', 'name', 'wallet_type', 'is_active')
        }),
        ('Financial Details', {
            'fields': ('balance', 'currency', 'account_number', 'bank_name')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'mse', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'mse__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User & MSE', {
            'fields': ('user', 'mse')
        }),
        ('Role Information', {
            'fields': ('role', 'permissions', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
