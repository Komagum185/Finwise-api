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


