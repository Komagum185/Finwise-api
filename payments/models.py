from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.utils import timezone

User = get_user_model()


class PaymentProvider(models.Model):
    """Payment provider configuration"""
    PROVIDER_TYPES = [
        ('mobile_money', 'Mobile Money'),
        ('bank', 'Bank Transfer'),
        ('card', 'Card Payment'),
        ('qr', 'QR Payment'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    provider_id = models.CharField(max_length=50, unique=True)  # e.g., 'mtn_uganda'
    type = models.CharField(max_length=20, choices=PROVIDER_TYPES)
    country = models.CharField(max_length=10)  # ISO country code
    currency = models.CharField(max_length=3)  # ISO currency code
    
    # Fee structure
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Limits
    min_amount = models.DecimalField(max_digits=15, decimal_places=2)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Configuration
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    webhook_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Payment Provider"
        verbose_name_plural = "Payment Providers"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.country})"
    
    def calculate_fees(self, amount):
        """Calculate fees for a given amount"""
        percentage_fee = (amount * self.fee_percentage) / 100
        total_fee = percentage_fee + self.fee_fixed
        return total_fee
    
    def is_amount_valid(self, amount):
        """Check if amount is within provider limits"""
        return self.min_amount <= amount <= self.max_amount


class QRPayment(models.Model):
    """QR Code Payment"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_qr_payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='UGX')
    description = models.CharField(max_length=255)
    
    # QR Code data
    qr_code = models.TextField()  # Base64 encoded QR code
    qr_url = models.URLField(blank=True)  # URL for QR code
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Payment details
    provider = models.ForeignKey(PaymentProvider, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    payer_phone = models.CharField(max_length=20, blank=True)
    payer_name = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "QR Payment"
        verbose_name_plural = "QR Payments"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"QR Payment {self.id} - {self.amount} {self.currency}"
    
    def is_expired(self):
        """Check if QR payment has expired"""
        return timezone.now() > self.expires_at
    
    def mark_completed(self, transaction_id=None, payer_phone=None, payer_name=None):
        """Mark QR payment as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if transaction_id:
            self.transaction_id = transaction_id
        if payer_phone:
            self.payer_phone = payer_phone
        if payer_name:
            self.payer_name = payer_name
        self.save()


class ScheduledTransfer(models.Model):
    """Scheduled Transfer"""
    FREQUENCY_CHOICES = [
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_scheduled_transfers')
    
    # Transfer details
    from_wallet = models.CharField(max_length=100)  # Wallet ID or account
    to_wallet = models.CharField(max_length=100, blank=True)  # For internal transfers
    phone_number = models.CharField(max_length=20, blank=True)  # For mobile money
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='UGX')
    description = models.CharField(max_length=255)
    
    # Scheduling
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='once')
    next_execution = models.DateTimeField()
    last_execution = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Provider
    provider = models.ForeignKey(PaymentProvider, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Scheduled Transfer"
        verbose_name_plural = "Scheduled Transfers"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Scheduled Transfer {self.id} - {self.amount} {self.currency}"
    
    def is_due(self):
        """Check if transfer is due for execution"""
        return timezone.now() >= self.next_execution
    
    def calculate_next_execution(self):
        """Calculate next execution date based on frequency"""
        if self.frequency == 'once':
            return None
        elif self.frequency == 'daily':
            return self.next_execution + timezone.timedelta(days=1)
        elif self.frequency == 'weekly':
            return self.next_execution + timezone.timedelta(weeks=1)
        elif self.frequency == 'monthly':
            return self.next_execution + timezone.timedelta(days=30)
        return None


class PaymentTransaction(models.Model):
    """Payment Transaction"""
    TRANSACTION_TYPES = [
        ('qr_payment', 'QR Payment'),
        ('scheduled_transfer', 'Scheduled Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('card_payment', 'Card Payment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments_payment_transactions')
    
    # Transaction details
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='UGX')
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Provider and reference
    provider = models.ForeignKey(PaymentProvider, on_delete=models.SET_NULL, null=True)
    reference = models.CharField(max_length=100, unique=True)
    external_transaction_id = models.CharField(max_length=100, blank=True)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Related objects
    qr_payment = models.ForeignKey(QRPayment, on_delete=models.SET_NULL, null=True, blank=True)
    scheduled_transfer = models.ForeignKey(ScheduledTransfer, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Additional data
    description = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.reference} - {self.amount} {self.currency}"
    
    def calculate_net_amount(self):
        """Calculate net amount after fees"""
        self.net_amount = self.amount - self.fees
        return self.net_amount
    
    def mark_completed(self, external_transaction_id=None):
        """Mark transaction as completed"""
        self.status = 'completed'
        self.processed_at = timezone.now()
        if external_transaction_id:
            self.external_transaction_id = external_transaction_id
        self.save()
    
    def mark_failed(self, error_message=None):
        """Mark transaction as failed"""
        self.status = 'failed'
        if error_message:
            self.metadata['error_message'] = error_message
        self.save()
