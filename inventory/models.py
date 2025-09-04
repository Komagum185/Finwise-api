from django.db import models
from decimal import Decimal
import uuid


class InventoryItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mse = models.ForeignKey('mse.MSE', on_delete=models.CASCADE, related_name='inventory_items')
    product_name = models.CharField(max_length=200)
    quantity_in = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    quantity_out = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['mse', 'product_name']

    @property
    def available_quantity(self):
        return self.quantity_in - self.quantity_out


class InventoryMovement(models.Model):
    """Model to track inventory movements (in/out transactions)"""
    MOVEMENT_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Stock Adjustment'),
        ('transfer', 'Transfer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mse = models.ForeignKey('mse.MSE', on_delete=models.CASCADE, related_name='inventory_movements')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    movement_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-movement_date']
    
    def __str__(self):
        return f"{self.movement_type} - {self.quantity} {self.inventory_item.product_name}"


