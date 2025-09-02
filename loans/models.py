from django.db import models
from decimal import Decimal
import uuid


class LoanProduct(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    repayment_period_months = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']


class GroupLoan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('disbursed', 'Disbursed'),
        ('repaid', 'Repaid'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='loans')
    product = models.ForeignKey(LoanProduct, on_delete=models.PROTECT, related_name='group_loans')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey('authentication.CustomUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_group_loans')
    approved_at = models.DateTimeField(null=True, blank=True)
    disbursed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class GroupLoanRepayment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(GroupLoan, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    repaid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-repaid_at']


