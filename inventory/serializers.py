from rest_framework import serializers
from .models import InventoryItem, InventoryMovement


class InventoryItemSerializer(serializers.ModelSerializer):
    available_quantity = serializers.ReadOnlyField()
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'mse', 'product_name', 'quantity_in', 'quantity_out',
            'unit_price', 'available_quantity', 'created_at', 'updated_at'
        ]


class InventoryMovementSerializer(serializers.ModelSerializer):
    mse_name = serializers.CharField(source='mse.first_name', read_only=True)
    product_name = serializers.CharField(source='inventory_item.product_name', read_only=True)
    
    class Meta:
        model = InventoryMovement
        fields = [
            'id', 'mse', 'mse_name', 'inventory_item', 'product_name',
            'movement_type', 'quantity', 'unit_price', 'reference_number',
            'notes', 'movement_date'
        ]


