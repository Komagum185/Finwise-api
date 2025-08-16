from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid
from django.utils import timezone

User = get_user_model()


class Customer(models.Model):
    """Customer model for managing customer relationships"""
    CUSTOMER_TYPES = [
        ('regular', 'Regular'),
        ('wholesale', 'Wholesale'),
        ('retail', 'Retail'),
        ('vip', 'VIP'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='regular')
    total_purchases = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    last_purchase = models.DateField(blank=True, null=True)
    average_order_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    loyalty_points = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, 
                               validators=[MinValueValidator(0), MaxValueValidator(5)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    favorite_products = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        unique_together = ['user', 'phone']
    
    def __str__(self):
        return f"{self.name} ({self.phone})"
    
    def clean(self):
        if self.rating < 0 or self.rating > 5:
            raise ValidationError("Rating must be between 0 and 5")
        if self.total_purchases < 0:
            raise ValidationError("Total purchases cannot be negative")
        if self.total_spent < 0:
            raise ValidationError("Total spent cannot be negative")
    
    def save(self, *args, **kwargs):
        self.clean()
        # Calculate average order value
        if self.total_purchases > 0:
            self.average_order_value = self.total_spent / self.total_purchases
        super().save(*args, **kwargs)
    
    def update_purchase_stats(self, amount):
        """Update customer purchase statistics"""
        self.total_purchases += 1
        self.total_spent += amount
        self.last_purchase = timezone.now().date()
        self.save()
    
    def add_loyalty_points(self, points):
        """Add loyalty points to customer"""
        self.loyalty_points += points
        self.save()
    
    def get_customer_tier(self):
        """Get customer tier based on total spent"""
        if self.total_spent >= 10000:
            return 'VIP'
        elif self.total_spent >= 5000:
            return 'Wholesale'
        elif self.total_spent >= 1000:
            return 'Retail'
        else:
            return 'Regular'


class CustomerFeedback(models.Model):
    """Customer feedback and ratings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_feedback')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    product = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = "Customer Feedback"
        verbose_name_plural = "Customer Feedback"
    
    def __str__(self):
        return f"{self.customer.name} - {self.rating}/5 - {self.date}"
    
    def clean(self):
        if self.rating < 1 or self.rating > 5:
            raise ValidationError("Rating must be between 1 and 5")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Update customer average rating
        self.update_customer_rating()
    
    def update_customer_rating(self):
        """Update customer's average rating"""
        customer = self.customer
        feedback_ratings = CustomerFeedback.objects.filter(customer=customer).values_list('rating', flat=True)
        if feedback_ratings:
            avg_rating = sum(feedback_ratings) / len(feedback_ratings)
            customer.rating = round(avg_rating, 2)
            customer.save()


class SMSCampaign(models.Model):
    """SMS marketing campaigns"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sms_campaigns')
    name = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    recipients = models.JSONField(help_text="List of customer IDs or phone numbers")
    scheduled_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    sent_date = models.DateTimeField(blank=True, null=True)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "SMS Campaign"
        verbose_name_plural = "SMS Campaigns"
    
    def __str__(self):
        return f"{self.name or 'SMS Campaign'} - {self.get_status_display()}"
    
    def clean(self):
        if not self.message.strip():
            raise ValidationError("Message cannot be empty")
        if len(self.message) > 160:
            raise ValidationError("SMS message cannot exceed 160 characters")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def get_total_recipients(self):
        """Get total number of recipients"""
        if isinstance(self.recipients, list):
            return len(self.recipients)
        return 0
    
    def get_success_rate(self):
        """Calculate success rate percentage"""
        total = self.success_count + self.failure_count
        if total > 0:
            return (self.success_count / total) * 100
        return 0
    
    def mark_as_sent(self, success_count=0, failure_count=0):
        """Mark campaign as sent with delivery statistics"""
        self.status = 'sent'
        self.sent_date = timezone.now()
        self.success_count = success_count
        self.failure_count = failure_count
        self.save()
    
    def mark_as_failed(self):
        """Mark campaign as failed"""
        self.status = 'failed'
        self.sent_date = timezone.now()
        self.save()
