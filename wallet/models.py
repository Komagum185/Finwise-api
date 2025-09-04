from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid
from django.utils import timezone


class Wallet(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='wallet'
    )
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.owner.username} Wallet - Balance: {self.balance}"


class WalletTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('loan_disbursement', 'Loan Disbursement'),
        ('loan_repayment', 'Loan Repayment'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('fee', 'Fee'),
        ('adjustment', 'Balance Adjustment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey('mse.Wallet', on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction details
    transaction_type = models.CharField(max_length=25, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='UGX')
    
    # Balance tracking
    balance_before = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Related entities
    related_loan = models.ForeignKey('loans.GroupLoan', on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='wallet_transactions')
    related_transaction = models.ForeignKey('markets.Transaction', on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='wallet_transactions')
    
    # Additional information
    reference_number = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Processing information
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='processed_transactions')
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallet_transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wallet.mse.full_name} - {self.transaction_type} {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        # Calculate balance after transaction
        if self.transaction_type in ['deposit', 'loan_disbursement', 'refund']:
            self.balance_after = self.balance_before + self.amount
        elif self.transaction_type in ['withdrawal', 'loan_repayment', 'payment', 'fee']:
            self.balance_after = self.balance_before - self.amount
        elif self.transaction_type == 'transfer':
            # For transfers, balance change depends on direction
            pass
        
        super().save(*args, **kwargs)
    
    @property
    def is_credit(self):
        """Check if transaction increases wallet balance"""
        return self.transaction_type in ['deposit', 'loan_disbursement', 'refund']
    
    @property
    def is_debit(self):
        """Check if transaction decreases wallet balance"""
        return self.transaction_type in ['withdrawal', 'loan_repayment', 'payment', 'fee']
    
    def process_transaction(self, processed_by_user):
        """Process the transaction"""
        if self.status == 'pending':
            self.status = 'completed'
            self.processed_by = processed_by_user
            self.processed_at = timezone.now()
            self.save()
            
            # Update wallet balance
            wallet = self.wallet
            wallet.balance = self.balance_after
            wallet.last_transaction_date = timezone.now()
            wallet.save()
