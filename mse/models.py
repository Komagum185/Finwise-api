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
    assigned_agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='assigned_mses', help_text="Agent assigned to manage this MSE")

    # Basic information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    nin = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    profile_image = models.ImageField(upload_to='mse_profiles/', blank=True, null=True)
    
    # Business information
    category = models.ForeignKey(MSECategory, on_delete=models.PROTECT, related_name='mses')
    location = models.CharField(max_length=255, blank=True)
    business_name = models.CharField(max_length=200, blank=True, help_text="Official business name")
    business_type = models.CharField(max_length=100, blank=True, help_text="Type of business")
    registration_number = models.CharField(max_length=50, blank=True, help_text="Business registration number")
    
    # Status and approval
    status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default='pending')
    approval_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='approved_mses')
    
    # Financial information
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    employee_count = models.PositiveIntegerField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mses'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.category.name})"
    
    def save(self, *args, **kwargs):
        # Auto-assign agent if not assigned and owner has an assigned agent
        if not self.assigned_agent and self.owner.assigned_agent:
            self.assigned_agent = self.owner.assigned_agent
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'


class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mse = models.OneToOneField(MSE, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='UGX')
    
    # Additional wallet information
    account_number = models.CharField(max_length=20, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_transaction_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mse_wallets'

    def __str__(self):
        return f"{self.mse.id} - {self.balance} {self.currency}"
    
    def save(self, *args, **kwargs):
        # Generate account number if not provided
        if not self.account_number:
            self.account_number = f"W{self.mse.id.hex[:8].upper()}"
        super().save(*args, **kwargs)


