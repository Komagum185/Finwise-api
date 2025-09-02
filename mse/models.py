from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid


class MSECategory(models.Model):
    CATEGORY_CHOICES = [
        ('input', 'Input'),
        ('producer', 'Producer'),
        ('output', 'Output'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mse_categories'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class MSE(models.Model):
    APPROVAL_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mse_accounts')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    nin = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    profile_image = models.ImageField(upload_to='mse_profiles/', blank=True, null=True)
    category = models.ForeignKey(MSECategory, on_delete=models.PROTECT, related_name='mses')
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mses'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.category.name})"


class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mse = models.OneToOneField(MSE, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='UGX')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mse_wallets'

    def __str__(self):
        return f"{self.mse.id} - {self.balance} {self.currency}"


