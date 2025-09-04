from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid
from django.utils import timezone


class LoanProduct(models.Model):
    LOAN_TYPE_CHOICES = [
        ('business', 'Business Loan'),
        ('agriculture', 'Agricultural Loan'),
        ('equipment', 'Equipment Loan'),
        ('working_capital', 'Working Capital'),
        ('emergency', 'Emergency Loan'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPE_CHOICES)
    
    # Loan terms
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual interest rate in percentage")
    term_min = models.PositiveIntegerField(help_text="Minimum term in months")
    term_max = models.PositiveIntegerField(help_text="Maximum term in months")
    
    # Requirements
    min_credit_score = models.PositiveIntegerField(null=True, blank=True)
    required_documents = models.JSONField(default=list, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loan_products'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.get_loan_type_display()}"


class GroupLoan(models.Model):
    LOAN_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mse = models.ForeignKey('mse.MSE', on_delete=models.CASCADE, related_name='loans')
    loan_product = models.ForeignKey(LoanProduct, on_delete=models.PROTECT, related_name='loans', null=True, blank=True)
    assigned_agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='assigned_loans', help_text="Agent assigned to manage this loan")
    
    # Loan details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    term_months = models.PositiveIntegerField(default=12)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))
    
    # Status and approval
    status = models.CharField(max_length=20, choices=LOAN_STATUS_CHOICES, default='pending')
    approval_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='approved_loans')
    
    # Disbursement
    disbursement_date = models.DateTimeField(null=True, blank=True)
    disbursement_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Financial tracking
    total_interest = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_principal_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Additional information
    purpose = models.TextField(blank=True)
    collateral = models.TextField(blank=True)
    guarantor_name = models.CharField(max_length=200, blank=True)
    guarantor_phone = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'group_loans'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.mse.full_name} - {self.amount} UGX ({self.status})"
    
    def save(self, *args, **kwargs):
        # Auto-assign agent if not assigned and MSE has an assigned agent
        if not self.assigned_agent and self.mse.assigned_agent:
            self.assigned_agent = self.mse.assigned_agent
        
        # Calculate outstanding balance
        if self.total_principal_paid > 0:
            self.outstanding_balance = self.amount - self.total_principal_paid
        
        super().save(*args, **kwargs)
    
    @property
    def monthly_payment(self):
        """Calculate monthly payment using simple interest"""
        if self.term_months > 0:
            monthly_rate = self.interest_rate / 100 / 12
            if monthly_rate > 0:
                return (self.amount * monthly_rate * (1 + monthly_rate) ** self.term_months) / ((1 + monthly_rate) ** self.term_months - 1)
        return self.amount / self.term_months
    
    @property
    def is_overdue(self):
        """Check if loan is overdue"""
        if self.status == 'active':
            # Calculate expected payments vs actual payments
            # This is a simplified check
            pass
        return False


class GroupLoanRepayment(models.Model):
    REPAYMENT_TYPE_CHOICES = [
        ('principal', 'Principal'),
        ('interest', 'Interest'),
        ('penalty', 'Penalty'),
        ('fees', 'Fees'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(GroupLoan, on_delete=models.CASCADE, related_name='repayments')
    
    # Repayment details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    repayment_type = models.CharField(max_length=20, choices=REPAYMENT_TYPE_CHOICES)
    payment_method = models.CharField(max_length=50, blank=True)
    
    # Status
    is_confirmed = models.BooleanField(default=False)
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='confirmed_repayments')
    
    # Additional information
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    payment_date = models.DateTimeField(default=timezone.now)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'group_loan_repayments'
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.loan.mse.full_name} - {self.amount} UGX ({self.repayment_type})"
    
    def confirm_payment(self, confirmed_by_user):
        """Confirm the payment"""
        if not self.is_confirmed:
            self.is_confirmed = True
            self.confirmed_by = confirmed_by_user
            self.confirmed_at = timezone.now()
            self.save()
            
            # Update loan totals
            loan = self.loan
            if self.repayment_type == 'principal':
                loan.total_principal_paid += self.amount
            elif self.repayment_type == 'interest':
                loan.total_interest += self.amount
            
            loan.save()


