from django.contrib import admin
from .models import Market, Producer, Customer, Product, BusinessTransaction


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ['name', 'mse', 'market_type', 'location', 'is_active']
    list_filter = ['market_type', 'is_active', 'created_at']
    search_fields = ['name', 'mse__name', 'location']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Producer)
class ProducerAdmin(admin.ModelAdmin):
    list_display = ['name', 'mse', 'contact_person', 'phone', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'mse__name', 'contact_person', 'products_supplied']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'mse', 'contact_person', 'credit_limit', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'mse__name', 'contact_person', 'email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'mse', 'product_type', 'unit_price', 'stock_quantity', 'is_active']
    list_filter = ['product_type', 'is_active', 'created_at']
    search_fields = ['name', 'mse__name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BusinessTransaction)
class BusinessTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_type', 'mse', 'amount', 'currency', 'status', 'transaction_date']
    list_filter = ['transaction_type', 'status', 'currency', 'transaction_date']
    search_fields = ['description', 'reference_number', 'mse__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'transaction_date'
