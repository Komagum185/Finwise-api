from django.contrib import admin
from .models import InventoryItem, InventoryMovement


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = [
        'product_name', 'mse', 'available_quantity', 'unit_price', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['product_name', 'mse__first_name', 'mse__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['product_name']


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = [
        'inventory_item', 'movement_type', 'quantity', 'reference_number', 'movement_date'
    ]
    list_filter = ['movement_type', 'movement_date']
    search_fields = ['inventory_item__product_name', 'reference_number', 'notes']
    readonly_fields = ['movement_date']
    ordering = ['-movement_date']
