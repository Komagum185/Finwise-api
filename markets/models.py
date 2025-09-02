from django.db import models
from decimal import Decimal
import uuid


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mse = models.ForeignKey('mse.MSE', on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['mse', 'phone_number']


class Supplier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mse = models.ForeignKey('mse.MSE', on_delete=models.CASCADE, related_name='suppliers')
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['mse', 'phone_number']


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mse = models.ForeignKey('mse.MSE', on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    unit = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mse = models.ForeignKey('mse.MSE', on_delete=models.CASCADE, related_name='market_transactions')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='transactions')
    counterparty_name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mse = models.ForeignKey('mse.MSE', on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)


