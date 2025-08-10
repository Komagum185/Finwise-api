from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid
from django.utils import timezone

User = get_user_model()


class Category(models.Model):
    """Financial transaction categories"""
    CATEGORY_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('both', 'Both'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES, default='expense')
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class or emoji")
    color = models.CharField(max_length=7, blank=True, help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Budget(models.Model):
    """Monthly budget tracking"""
    PERIODS = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('weekly', 'Weekly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    period = models.CharField(max_length=10, choices=PERIODS, default='monthly')
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'category', 'start_date']
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.category.name} - {self.amount}"
    
    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("End date must be after start date")
    
    @property
    def spent_amount(self):
        """Calculate total spent amount for this budget period"""
        from .models import Transaction
        return Transaction.objects.filter(
            user=self.user,
            category=self.category,
            date__gte=self.start_date,
            date__lte=self.end_date,
            transaction_type='expense'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    
    @property
    def remaining_amount(self):
        """Calculate remaining budget amount"""
        return self.amount - self.spent_amount
    
    @property
    def spent_percentage(self):
        """Calculate percentage of budget spent"""
        if self.amount == 0:
            return 0
        return (self.spent_amount / self.amount) * 100


class Goal(models.Model):
    """Financial goals and savings targets"""
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
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    target_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    priority = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def clean(self):
        if self.target_date and self.target_date < timezone.now().date():
            raise ValidationError("Target date cannot be in the past")
        if self.current_amount > self.target_amount:
            raise ValidationError("Current amount cannot exceed target amount")
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.target_amount == 0:
            return 0
        return (self.current_amount / self.target_amount) * 100
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to reach goal"""
        return self.target_amount - self.current_amount
    
    @property
    def is_completed(self):
        """Check if goal is completed"""
        return self.current_amount >= self.target_amount


class Transaction(models.Model):
    """Enhanced financial transaction model"""
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    description = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='transactions')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    notes = models.TextField(blank=True)
    receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True)
    location = models.CharField(max_length=200, blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'transaction_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.description} - {self.amount}"
    
    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Amount must be greater than zero")
        if not self.description:
            raise ValidationError("Description is required")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    """Extended user profile with financial preferences"""
    CURRENCY_CHOICES = [
        ('UGX', 'Uganda Shillings'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('JPY', 'Japanese Yen'),
        ('CAD', 'Canadian Dollar'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UGX')
    monthly_income = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    emergency_fund_target = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notification_preferences = models.JSONField(default=dict)
    financial_goals = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - Profile"
    
    @property
    def total_balance(self):
        """Calculate total balance from all transactions"""
        income = self.user.transactions.filter(
            transaction_type='income',
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        expenses = self.user.transactions.filter(
            transaction_type='expense',
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        return income - expenses


class RecurringTransaction(models.Model):
    """Model for recurring transactions"""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recurring_transactions')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    transaction_type = models.CharField(max_length=10, choices=Transaction.TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    next_due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['next_due_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.description} ({self.frequency})"
    
    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("End date must be after start date")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
