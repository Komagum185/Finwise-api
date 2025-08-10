from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from mses.models import MSE, Wallet


class Market(models.Model):
    """Market model for business transactions"""
    MARKET_TYPES = [
        ('input', 'Input Market'),
        ('output', 'Output Market'),
    ]
    
    mse = models.ForeignKey(MSE, on_delete=models.CASCADE, related_name='markets')
    name = models.CharField(max_length=200)
    market_type = models.CharField(max_length=20, choices=MARKET_TYPES, default='output')
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_market_type_display()})"
    
    def clean(self):
        if not self.name:
            raise ValidationError("Market name is required")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Producer(models.Model):
    """Producer/Supplier model"""
    mse = models.ForeignKey(MSE, on_delete=models.CASCADE, related_name='producers')
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    products_supplied = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.mse.name}"
    
    def clean(self):
        if not self.name:
            raise ValidationError("Producer name is required")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Customer(models.Model):
    """Customer model"""
    mse = models.ForeignKey(MSE, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    payment_terms = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.mse.name}"
    
    def clean(self):
        if not self.name:
            raise ValidationError("Customer name is required")
        if self.credit_limit < 0:
            raise ValidationError("Credit limit cannot be negative")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Product(models.Model):
    """Product model"""
    PRODUCT_TYPES = [
        ('goods', 'Goods'),
        ('services', 'Services'),
    ]
    
    mse = models.ForeignKey(MSE, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='goods')
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    cost_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    stock_quantity = models.IntegerField(default=0)
    unit = models.CharField(max_length=20, default='piece')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.mse.name}"
    
    def clean(self):
        if not self.name:
            raise ValidationError("Product name is required")
        if self.unit_price < 0:
            raise ValidationError("Unit price cannot be negative")
        if self.cost_price < 0:
            raise ValidationError("Cost price cannot be negative")
        if self.stock_quantity < 0:
            raise ValidationError("Stock quantity cannot be negative")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class BusinessTransaction(models.Model):
    """Business transaction model"""
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('expense', 'Expense'),
        ('income', 'Income'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    mse = models.ForeignKey(MSE, on_delete=models.CASCADE, related_name='business_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    description = models.TextField(blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    transaction_date = models.DateTimeField()
    wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, null=True, blank=True)
    producer = models.ForeignKey(Producer, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} {self.currency}"
    
    def clean(self):
        if not self.amount or self.amount <= 0:
            raise ValidationError("Amount must be greater than zero")
        if not self.transaction_date:
            raise ValidationError("Transaction date is required")
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
