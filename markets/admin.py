from django.contrib import admin
from .models import Customer, Supplier, Product, Transaction, Notification


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'mse', 'customer_type', 'phone', 'is_active', 'created_at'
    ]
    list_filter = ['customer_type', 'is_active', 'created_at']
    search_fields = ['name', 'mse__first_name', 'mse__last_name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'mse', 'supplier_type', 'phone', 'is_active', 'rating', 'created_at'
    ]
    list_filter = ['supplier_type', 'is_active', 'rating', 'created_at']
    search_fields = ['name', 'mse__first_name', 'mse__last_name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'mse', 'category', 'unit_price', 'stock_quantity', 'created_at'
    ]
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'mse__first_name', 'mse__last_name', 'category']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'mse', 'transaction_type', 'amount', 'currency', 'payment_status', 'created_at'
    ]
    list_filter = ['transaction_type', 'payment_status', 'currency', 'created_at']
    search_fields = ['id', 'mse__first_name', 'mse__last_name', 'reference_number']
    readonly_fields = ['created_at', 'updated_at', 'transaction_date']
    ordering = ['-created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'title', 'notification_type', 'is_read', 'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']
    ordering = ['-created_at']
