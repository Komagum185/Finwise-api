from rest_framework import serializers
from .models import InventoryItem


class InventoryItemSerializer(serializers.ModelSerializer):
    available_quantity = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = InventoryItem
        fields = ['id', 'mse', 'product_name', 'quantity_in', 'quantity_out', 'available_quantity', 'unit_price', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


