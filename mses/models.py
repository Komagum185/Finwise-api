from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class MSE(models.Model):
    """Base Micro and Small Enterprise model"""
    MSE_TYPES = [
        ('micro', 'Micro Enterprise'),
        ('small', 'Small Enterprise'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    mse_type = models.CharField(max_length=10, choices=MSE_TYPES, default='micro')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    registration_number = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    business_type = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "MSE"
        verbose_name_plural = "MSEs"
    
    def __str__(self):
        return f"{self.name} ({self.get_mse_type_display()})"
    
    def clean(self):
        if not self.name:
            raise ValidationError("MSE name is required")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class InputMSE(models.Model):
    """Input Market MSE - Focuses on sourcing raw materials and inputs"""
    mse = models.OneToOneField(MSE, on_delete=models.CASCADE, related_name='input_mse')
    
    # Input-specific fields
    input_categories = models.JSONField(default=list, help_text="Categories of inputs sourced")
    supplier_network_size = models.IntegerField(default=0, help_text="Number of suppliers in network")
    average_order_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    lead_time_days = models.IntegerField(default=0, help_text="Average lead time in days")
    quality_standards = models.TextField(blank=True, help_text="Quality standards maintained")
    storage_capacity = models.CharField(max_length=100, blank=True, help_text="Storage capacity description")
    
    # Input sourcing details
    primary_inputs = models.JSONField(default=list, help_text="List of primary inputs sourced")
    seasonal_inputs = models.JSONField(default=list, help_text="Seasonal inputs and their periods")
    input_costs_tracking = models.BooleanField(default=True, help_text="Track input costs separately")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Input MSE"
        verbose_name_plural = "Input MSEs"
    
    def __str__(self):
        return f"Input MSE: {self.mse.name}"
    
    def get_total_input_value(self):
        """Calculate total value of inputs sourced"""
        from markets.models import BusinessTransaction
        transactions = BusinessTransaction.objects.filter(
            mse=self.mse,
            transaction_type='purchase',
            status='completed'
        )
        return sum(t.amount for t in transactions)


class OutputMSE(models.Model):
    """Output Market MSE - Focuses on selling products and services"""
    mse = models.OneToOneField(MSE, on_delete=models.CASCADE, related_name='output_mse')
    
    # Output-specific fields
    output_categories = models.JSONField(default=list, help_text="Categories of outputs sold")
    customer_network_size = models.IntegerField(default=0, help_text="Number of customers in network")
    average_sale_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    sales_channels = models.JSONField(default=list, help_text="Sales channels used")
    marketing_strategy = models.TextField(blank=True, help_text="Marketing strategy description")
    
    # Sales and distribution details
    primary_products = models.JSONField(default=list, help_text="List of primary products/services")
    seasonal_products = models.JSONField(default=list, help_text="Seasonal products and their periods")
    pricing_strategy = models.CharField(max_length=100, blank=True, help_text="Pricing strategy used")
    delivery_methods = models.JSONField(default=list, help_text="Delivery methods offered")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Output MSE"
        verbose_name_plural = "Output MSEs"
    
    def __str__(self):
        return f"Output MSE: {self.mse.name}"
    
    def get_total_sales_value(self):
        """Calculate total value of sales"""
        from markets.models import BusinessTransaction
        transactions = BusinessTransaction.objects.filter(
            mse=self.mse,
            transaction_type='sale',
            status='completed'
        )
        return sum(t.amount for t in transactions)


class ProductionMSE(models.Model):
    """Production MSE - Focuses on manufacturing and processing"""
    mse = models.OneToOneField(MSE, on_delete=models.CASCADE, related_name='production_mse')
    
    # Production-specific fields
    production_capacity = models.CharField(max_length=100, blank=True, help_text="Production capacity description")
    production_process = models.TextField(blank=True, help_text="Production process description")
    equipment_list = models.JSONField(default=list, help_text="List of production equipment")
    quality_control = models.TextField(blank=True, help_text="Quality control procedures")
    
    # Manufacturing details
    raw_materials_required = models.JSONField(default=list, help_text="Raw materials required for production")
    production_cycle_time = models.CharField(max_length=50, blank=True, help_text="Production cycle time")
    waste_management = models.TextField(blank=True, help_text="Waste management procedures")
    safety_protocols = models.TextField(blank=True, help_text="Safety protocols")
    
    # Capacity and efficiency
    daily_production_target = models.IntegerField(default=0, help_text="Daily production target")
    efficiency_metrics = models.JSONField(default=dict, help_text="Production efficiency metrics")
    maintenance_schedule = models.TextField(blank=True, help_text="Equipment maintenance schedule")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Production MSE"
        verbose_name_plural = "Production MSEs"
    
    def __str__(self):
        return f"Production MSE: {self.mse.name}"
    
    def get_production_efficiency(self):
        """Calculate production efficiency"""
        if self.daily_production_target > 0:
            # This would need to be calculated based on actual production data
            return 0.0
        return 0.0


class MSECategory(models.Model):
    """MSE Category model to track which category an MSE belongs to"""
    MSE_CATEGORIES = [
        ('input', 'Input MSE'),
        ('output', 'Output MSE'),
        ('production', 'Production MSE'),
        ('hybrid', 'Hybrid MSE'),  # MSE that operates in multiple categories
    ]
    
    mse = models.OneToOneField(MSE, on_delete=models.CASCADE, related_name='category')
    primary_category = models.CharField(max_length=20, choices=MSE_CATEGORIES)
    secondary_categories = models.JSONField(default=list, help_text="Secondary categories if hybrid")
    category_description = models.TextField(blank=True, help_text="Description of business category")
    
    # Category-specific metrics
    category_performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    category_growth_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "MSE Category"
        verbose_name_plural = "MSE Categories"
    
    def __str__(self):
        return f"{self.mse.name} - {self.get_primary_category_display()}"
    
    def get_category_details(self):
        """Get category-specific details"""
        if self.primary_category == 'input' and hasattr(self.mse, 'input_mse'):
            return self.mse.input_mse
        elif self.primary_category == 'output' and hasattr(self.mse, 'output_mse'):
            return self.mse.output_mse
        elif self.primary_category == 'production' and hasattr(self.mse, 'production_mse'):
            return self.mse.production_mse
        return None


class Wallet(models.Model):
    """Business wallet model"""
    WALLET_TYPES = [
        ('cash', 'Cash'),
        ('bank', 'Bank Account'),
        ('mobile', 'Mobile Money'),
        ('digital', 'Digital Wallet'),
    ]
    
    mse = models.ForeignKey(MSE, on_delete=models.CASCADE, related_name='wallets')
    name = models.CharField(max_length=100)
    wallet_type = models.CharField(max_length=20, choices=WALLET_TYPES, default='cash')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    account_number = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.mse.name}"
    
    def clean(self):
        if not self.name:
            raise ValidationError("Wallet name is required")
        if self.balance < 0:
            raise ValidationError("Balance cannot be negative")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class WalletTransaction(models.Model):
    """Wallet transaction model for tracking all wallet activities"""
    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('transfer', 'Transfer'),
        ('withdrawal', 'Withdrawal'),
        ('deposit', 'Deposit'),
    ]
    
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    CATEGORY_CHOICES = [
        ('payment', 'Payment'),
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('transfer', 'Transfer'),
        ('fee', 'Fee'),
        ('refund', 'Refund'),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True)
    related_transaction = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_transactions')
    transaction_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-transaction_date']
        verbose_name = "Wallet Transaction"
        verbose_name_plural = "Wallet Transactions"
    
    def __str__(self):
        return f"{self.wallet.name} - {self.get_transaction_type_display()} - {self.amount}"
    
    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Transaction amount must be positive")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
        # Update wallet balance based on transaction
        if self.status == 'completed':
            if self.transaction_type in ['credit', 'deposit']:
                self.wallet.balance += self.amount
            elif self.transaction_type in ['debit', 'withdrawal']:
                self.wallet.balance -= self.amount
            elif self.transaction_type == 'transfer':
                # Handle transfer logic
                pass
            self.wallet.save()


class UserRole(models.Model):
    """User role model for business management"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
        ('viewer', 'Viewer'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mse = models.ForeignKey(MSE, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    permissions = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'mse']
    
    def __str__(self):
        return f"{self.user.username} - {self.role} at {self.mse.name}"
    
    def clean(self):
        if not self.user or not self.mse:
            raise ValidationError("User and MSE are required")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
