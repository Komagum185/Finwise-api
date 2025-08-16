from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db.models import Sum, Count
from django.utils import timezone
import uuid

# Import wallet models from mses app
from mses.models import Wallet as MSEWallet, WalletTransaction as MSEWalletTransaction


class Category(models.Model):
    """Category model for organizing transactions and budgets"""
    CATEGORY_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
        ('investment', 'Investment'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class or identifier")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class EnhancedWallet(models.Model):
    """Enhanced wallet model matching the TypeScript interface"""
    ACCOUNT_TYPES = [
        ('Business', 'Business'),
        ('Savings', 'Savings'),
        ('Investment', 'Investment'),
        ('Emergency', 'Emergency'),
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
        ('Pending', 'Pending'),
    ]
    
    # Core wallet fields
    mse_id = models.CharField(max_length=100, help_text="MSE identifier")
    mse_name = models.CharField(max_length=200, help_text="MSE business name")
    mse_code = models.CharField(max_length=50, help_text="MSE business code")
    account_number = models.CharField(max_length=100, unique=True, help_text="Unique account number")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='Business')
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    description = models.TextField(blank=True, help_text="Wallet description")
    
    # Metadata
    last_transaction = models.DateTimeField(null=True, blank=True)
    transaction_count = models.IntegerField(default=0)
    monthly_volume = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Enhanced Wallet"
        verbose_name_plural = "Enhanced Wallets"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.mse_name} - {self.account_type} ({self.account_number})"
    
    def clean(self):
        if self.balance < 0:
            raise ValidationError("Wallet balance cannot be negative")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def update_transaction_stats(self):
        """Update transaction count and monthly volume"""
        from .models import EnhancedWalletTransaction
        
        # Count total transactions
        self.transaction_count = EnhancedWalletTransaction.objects.filter(wallet=self).count()
        
        # Calculate monthly volume
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_transactions = EnhancedWalletTransaction.objects.filter(
            wallet=self,
            created_at__gte=month_start
        )
        self.monthly_volume = monthly_transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        # Update last transaction
        last_tx = monthly_transactions.order_by('-created_at').first()
        if last_tx:
            self.last_transaction = last_tx.created_at
        
        self.save()


class EnhancedWalletTransaction(models.Model):
    """Enhanced wallet transaction model matching the TypeScript interface"""
    TRANSACTION_TYPES = [
        ('Credit', 'Credit'),
        ('Debit', 'Debit'),
        ('Transfer', 'Transfer'),
        ('Withdrawal', 'Withdrawal'),
        ('Deposit', 'Deposit'),
    ]
    
    STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    CATEGORY_CHOICES = [
        ('Payment', 'Payment'),
        ('Purchase', 'Purchase'),
        ('Sale', 'Sale'),
        ('Transfer', 'Transfer'),
        ('Fee', 'Fee'),
        ('Refund', 'Refund'),
    ]
    
    # Core transaction fields
    wallet = models.ForeignKey(EnhancedWallet, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    # Optional fields
    reference = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True)
    related_transaction_id = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_transactions')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Enhanced Wallet Transaction"
        verbose_name_plural = "Enhanced Wallet Transactions"
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.type} - {self.amount} {self.wallet.currency} ({self.status})"
    
    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Transaction amount must be positive")
    
    def save(self, *args, **kwargs):
        self.clean()
        is_new = self.pk is None
        
        # Save the transaction
        super().save(*args, **kwargs)
        
        # Update wallet balance and stats
        if is_new and self.status == 'Completed':
            self.update_wallet_balance()
        
        # Update wallet transaction statistics
        self.wallet.update_transaction_stats()
    
    def update_wallet_balance(self):
        """Update wallet balance based on transaction"""
        if self.type == 'Credit' or self.type == 'Deposit':
            self.wallet.balance += self.amount
        elif self.type == 'Debit' or self.type == 'Withdrawal':
            self.wallet.balance -= self.amount
        elif self.type == 'Transfer':
            # Transfer logic handled separately
            pass
        
        self.wallet.save()


class WalletTransfer(models.Model):
    """Wallet transfer model for handling transfers between wallets"""
    from_wallet = models.ForeignKey(EnhancedWallet, on_delete=models.CASCADE, related_name='outgoing_transfers')
    to_wallet = models.ForeignKey(EnhancedWallet, on_delete=models.CASCADE, related_name='incoming_transfers')
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    description = models.TextField()
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=20, choices=EnhancedWalletTransaction.STATUS_CHOICES, default='Pending')
    
    # Transaction references
    debit_transaction = models.ForeignKey(EnhancedWalletTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='debit_transfer')
    credit_transaction = models.ForeignKey(EnhancedWalletTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='credit_transfer')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Wallet Transfer"
        verbose_name_plural = "Wallet Transfers"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Transfer: {self.from_wallet.account_number} → {self.to_wallet.account_number} ({self.amount})"
    
    def clean(self):
        if self.from_wallet == self.to_wallet:
            raise ValidationError("Cannot transfer to the same wallet")
        if self.amount <= 0:
            raise ValidationError("Transfer amount must be positive")
        if self.from_wallet.currency != self.to_wallet.currency:
            raise ValidationError("Cannot transfer between different currencies")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class WalletStatistics(models.Model):
    """Wallet statistics model for aggregated data"""
    wallet = models.OneToOneField(EnhancedWallet, on_delete=models.CASCADE, related_name='statistics')
    total_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    total_wallets = models.IntegerField(default=1)
    active_wallets = models.IntegerField(default=1)
    monthly_volume = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    monthly_transactions = models.IntegerField(default=0)
    currency = models.CharField(max_length=3, default='USD')
    
    # Historical data
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Wallet Statistics"
        verbose_name_plural = "Wallet Statistics"
    
    def __str__(self):
        return f"Stats for {self.wallet.mse_name}"
    
    def update_statistics(self):
        """Update all statistics for the wallet"""
        # Get all wallets for the same MSE
        mse_wallets = EnhancedWallet.objects.filter(mse_id=self.wallet.mse_id)
        self.total_wallets = mse_wallets.count()
        self.active_wallets = mse_wallets.filter(status='Active').count()
        
        # Calculate total balance across all wallets
        self.total_balance = mse_wallets.aggregate(total=Sum('balance'))['total'] or 0
        
        # Update monthly statistics
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_txs = EnhancedWalletTransaction.objects.filter(
            wallet__mse_id=self.wallet.mse_id,
            created_at__gte=month_start
        )
        self.monthly_transactions = monthly_txs.count()
        self.monthly_volume = monthly_txs.aggregate(total=Sum('amount'))['total'] or 0
        
        self.save()


class Transaction(models.Model):
    """Transaction model for financial transactions"""
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
        ('investment', 'Investment'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('bank', 'Bank'),
        ('card', 'Card'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic transaction details
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    
    # Transaction metadata
    transaction_date = models.DateTimeField()
    reference_number = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Related models
    wallet = models.ForeignKey(EnhancedWallet, on_delete=models.SET_NULL, null=True, blank=True, related_name='finance_transactions')
    
    # Additional fields
    receipt_image = models.URLField(blank=True, help_text="URL to receipt image")
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.title} - {self.amount} {self.currency}"
    
    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Transaction amount must be positive")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class BusinessHealth(models.Model):
    """Business health metrics and analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='business_health')
    financial_health = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    inventory_efficiency = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    customer_satisfaction = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-calculated_at']
        verbose_name = "Business Health"
        verbose_name_plural = "Business Health Metrics"
    
    def __str__(self):
        return f"{self.user.username} - Business Health - {self.calculated_at.strftime('%Y-%m-%d')}"
    
    def calculate_overall_score(self):
        """Calculate overall business health score"""
        scores = []
        if self.financial_health is not None:
            scores.append(self.financial_health)
        if self.inventory_efficiency is not None:
            scores.append(self.inventory_efficiency)
        if self.customer_satisfaction is not None:
            scores.append(self.customer_satisfaction)
        
        if scores:
            self.overall_score = sum(scores) / len(scores)
        else:
            self.overall_score = None
    
    def save(self, *args, **kwargs):
        self.calculate_overall_score()
        super().save(*args, **kwargs)
    
    def get_health_status(self):
        """Get health status based on overall score"""
        if self.overall_score is None:
            return 'unknown'
        elif self.overall_score >= 80:
            return 'excellent'
        elif self.overall_score >= 60:
            return 'good'
        elif self.overall_score >= 40:
            return 'fair'
        else:
            return 'poor'
    
    def get_recommendations_summary(self):
        """Get a summary of recommendations"""
        if not self.recommendations:
            return "No specific recommendations at this time."
        
        return f"{len(self.recommendations)} recommendations available"


class Budget(models.Model):
    """Budget model for financial planning"""
    BUDGET_TYPES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPES, default='monthly')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Budget amounts
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Time period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Categories and limits
    category_limits = models.JSONField(default=dict, help_text="Category-specific budget limits")
    
    # Notifications
    alert_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=80.00, help_text="Alert when spending reaches this percentage")
    notifications_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"
    
    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date")
        if self.total_amount <= 0:
            raise ValidationError("Budget amount must be positive")
    
    def save(self, *args, **kwargs):
        self.clean()
        # Calculate remaining amount
        self.remaining_amount = self.total_amount - self.spent_amount
        super().save(*args, **kwargs)
    
    def get_spending_percentage(self):
        """Calculate spending percentage"""
        if self.total_amount > 0:
            return (self.spent_amount / self.total_amount) * 100
        return 0
    
    def is_over_budget(self):
        """Check if budget is exceeded"""
        return self.spent_amount > self.total_amount


class Goal(models.Model):
    """Financial goal model for savings and targets"""
    GOAL_TYPES = [
        ('savings', 'Savings'),
        ('debt_payoff', 'Debt Payoff'),
        ('investment', 'Investment'),
        ('purchase', 'Purchase'),
        ('emergency_fund', 'Emergency Fund'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Goal amounts
    target_amount = models.DecimalField(max_digits=15, decimal_places=2)
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Time period
    target_date = models.DateField()
    start_date = models.DateField(auto_now_add=True)
    
    # Progress tracking
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    monthly_target = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Motivation
    motivation_note = models.TextField(blank=True)
    image_url = models.URLField(blank=True, help_text="Motivational image URL")
    
    # Notifications
    reminders_enabled = models.BooleanField(default=True)
    reminder_frequency = models.CharField(max_length=20, default='weekly', choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Financial Goal"
        verbose_name_plural = "Financial Goals"
        ordering = ['-target_date']
    
    def __str__(self):
        return f"{self.name} - {self.current_amount}/{self.target_amount}"
    
    def clean(self):
        if self.target_amount <= 0:
            raise ValidationError("Target amount must be positive")
        if self.target_date <= self.start_date:
            raise ValidationError("Target date must be in the future")
    
    def save(self, *args, **kwargs):
        self.clean()
        # Calculate remaining amount and progress
        self.remaining_amount = self.target_amount - self.current_amount
        if self.target_amount > 0:
            self.progress_percentage = (self.current_amount / self.target_amount) * 100
        super().save(*args, **kwargs)
    
    def is_completed(self):
        """Check if goal is completed"""
        return self.current_amount >= self.target_amount
    
    def get_days_remaining(self):
        """Calculate days remaining to target date"""
        from datetime import date
        today = date.today()
        return (self.target_date - today).days


class PaymentTransaction(models.Model):
    """Payment transaction model for mobile money and bank transfers"""
    TRANSACTION_TYPES = [
        ('send', 'Send'),
        ('receive', 'Receive'),
        ('withdraw', 'Withdraw'),
        ('deposit', 'Deposit'),
    ]
    
    PROVIDERS = [
        ('mtn', 'MTN Mobile Money'),
        ('airtel', 'Airtel Money'),
        ('bank', 'Bank Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    provider = models.CharField(max_length=20, choices=PROVIDERS)
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    fee = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    confirmation_code = models.CharField(max_length=50, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reference']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} via {self.get_provider_display()}"
    
    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Amount must be greater than zero")
        if self.fee < 0:
            raise ValidationError("Fee cannot be negative")
        if self.total_amount != self.amount + self.fee:
            raise ValidationError("Total amount must equal amount plus fee")
    
    def save(self, *args, **kwargs):
        self.clean()
        # Calculate total amount if not set
        if not self.total_amount:
            self.total_amount = self.amount + self.fee
        super().save(*args, **kwargs)
    
    def get_net_amount(self):
        """Get net amount after fees"""
        return self.amount - self.fee
    
    def is_successful(self):
        """Check if transaction was successful"""
        return self.status == 'completed'
    
    def can_be_cancelled(self):
        """Check if transaction can be cancelled"""
        return self.status in ['pending', 'processing']


class BulkPayment(models.Model):
    """Bulk payment model for sending multiple payments"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bulk_payments')
    name = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    recipient_count = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Bulk Payment"
        verbose_name_plural = "Bulk Payments"
    
    def __str__(self):
        return f"{self.name} - {self.recipient_count} recipients"
    
    def clean(self):
        if self.total_amount <= 0:
            raise ValidationError("Total amount must be greater than zero")
        if self.recipient_count <= 0:
            raise ValidationError("Recipient count must be greater than zero")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def get_successful_recipients(self):
        """Get count of successful recipients"""
        return self.recipients.filter(status='sent').count()
    
    def get_failed_recipients(self):
        """Get count of failed recipients"""
        return self.recipients.filter(status='failed').count()
    
    def get_pending_recipients(self):
        """Get count of pending recipients"""
        return self.recipients.filter(status='pending').count()
    
    def get_success_rate(self):
        """Calculate success rate percentage"""
        total = self.recipient_count
        if total > 0:
            successful = self.get_successful_recipients()
            return (successful / total) * 100
        return 0
    
    def can_be_processed(self):
        """Check if bulk payment can be processed"""
        return self.status in ['draft', 'scheduled']
    
    def mark_as_processing(self):
        """Mark bulk payment as processing"""
        self.status = 'processing'
        self.save()
    
    def mark_as_completed(self):
        """Mark bulk payment as completed"""
        self.status = 'completed'
        self.save()
    
    def mark_as_failed(self):
        """Mark bulk payment as failed"""
        self.status = 'failed'
        self.save()


class BulkPaymentRecipient(models.Model):
    """Individual recipient in a bulk payment"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bulk_payment = models.ForeignKey(BulkPayment, on_delete=models.CASCADE, related_name='recipients')
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Bulk Payment Recipient"
        verbose_name_plural = "Bulk Payment Recipients"
        unique_together = ['bulk_payment', 'phone_number']
    
    def __str__(self):
        return f"{self.name or self.phone_number} - {self.amount}"
    
    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Amount must be greater than zero")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def mark_as_sent(self, reference=None):
        """Mark recipient as sent"""
        self.status = 'sent'
        if reference:
            self.reference = reference
        self.save()
    
    def mark_as_failed(self, reference=None):
        """Mark recipient as failed"""
        self.status = 'failed'
        if reference:
            self.reference = reference
        self.save()

