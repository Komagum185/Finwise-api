from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()


class LoanApplication(models.Model):
    """Loan application model"""
    APPLICATION_STATUS = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mse = models.ForeignKey('mses.MSE', on_delete=models.CASCADE)
    
    # Loan details
    requested_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    purpose = models.TextField()
    business_plan = models.TextField(blank=True)
    collateral_description = models.TextField(blank=True)
    
    # Application metadata
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Risk assessment
    credit_score = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(300), MaxValueValidator(850)])
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
    ], blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Loan Application"
        verbose_name_plural = "Loan Applications"
    
    def __str__(self):
        return f"Loan Application {self.id} - {self.applicant.username} - {self.status}"
    
    def clean(self):
        if self.requested_amount <= 0:
            raise ValidationError("Requested amount must be positive")
    
    def save(self, *args, **kwargs):
        self.clean()
        if self.status == 'submitted' and not self.submitted_at:
            self.submitted_at = timezone.now()
        super().save(*args, **kwargs)


class Loan(models.Model):
    """Loan model for approved loans"""
    LOAN_STATUS = [
        ('active', 'Active'),
        ('paid_off', 'Paid Off'),
        ('defaulted', 'Defaulted'),
        ('cancelled', 'Cancelled'),
    ]
    
    LOAN_TYPES = [
        ('business', 'Business Loan'),
        ('working_capital', 'Working Capital'),
        ('equipment', 'Equipment Loan'),
        ('expansion', 'Expansion Loan'),
        ('emergency', 'Emergency Loan'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE)
    mse = models.ForeignKey('mses.MSE', on_delete=models.CASCADE)
    
    # Loan terms
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES)
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100.00'))])
    term_months = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(360)])
    
    # Payment schedule
    payment_frequency = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('biweekly', 'Bi-weekly'),
        ('weekly', 'Weekly'),
    ], default='monthly')
    
    # Loan status
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default='active')
    disbursed_at = models.DateTimeField(null=True, blank=True)
    maturity_date = models.DateField()
    
    # Financial tracking
    total_interest = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_paid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    outstanding_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Late payment tracking
    days_past_due = models.IntegerField(default=0)
    late_fees_charged = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Loan"
        verbose_name_plural = "Loans"
    
    def __str__(self):
        return f"Loan {self.id} - {self.mse.name} - {self.status}"
    
    def clean(self):
        if self.principal_amount <= 0:
            raise ValidationError("Principal amount must be positive")
        if self.interest_rate <= 0:
            raise ValidationError("Interest rate must be positive")
        if self.term_months <= 0:
            raise ValidationError("Term must be positive")
    
    def save(self, *args, **kwargs):
        self.clean()
        if not self.maturity_date:
            self.maturity_date = timezone.now().date() + timedelta(days=self.term_months * 30)
        super().save(*args, **kwargs)
    
    def calculate_monthly_payment(self):
        """Calculate monthly payment using amortization formula"""
        if self.interest_rate == 0:
            return self.principal_amount / self.term_months
        
        monthly_rate = self.interest_rate / 100 / 12
        if monthly_rate == 0:
            return self.principal_amount / self.term_months
        
        payment = self.principal_amount * (monthly_rate * (1 + monthly_rate) ** self.term_months) / ((1 + monthly_rate) ** self.term_months - 1)
        return round(payment, 2)
    
    def get_total_amount_due(self):
        """Get total amount due including principal and interest"""
        return self.principal_amount + self.total_interest
    
    def get_remaining_balance(self):
        """Get remaining balance after payments"""
        return self.get_total_amount_due() - self.total_paid


class LoanSchedule(models.Model):
    """Loan payment schedule"""
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('partial', 'Partially Paid'),
    ]
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='schedule')
    payment_number = models.IntegerField()
    due_date = models.DateField()
    principal_due = models.DecimalField(max_digits=15, decimal_places=2)
    interest_due = models.DecimalField(max_digits=15, decimal_places=2)
    total_due = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after_payment = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Payment tracking
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    payment_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Late payment tracking
    days_overdue = models.IntegerField(default=0)
    late_fees = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['payment_number']
        unique_together = ['loan', 'payment_number']
        verbose_name = "Loan Schedule"
        verbose_name_plural = "Loan Schedules"
    
    def __str__(self):
        return f"Payment {self.payment_number} - {self.loan.id} - {self.status}"
    
    def clean(self):
        if self.total_due != self.principal_due + self.interest_due:
            raise ValidationError("Total due must equal principal + interest")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def get_remaining_amount(self):
        """Get remaining amount to be paid"""
        return self.total_due - self.amount_paid
    
    def is_overdue(self):
        """Check if payment is overdue"""
        return self.due_date < timezone.now().date() and self.status != 'paid'
    
    def calculate_late_fees(self):
        """Calculate late fees if overdue"""
        if self.is_overdue():
            days_overdue = (timezone.now().date() - self.due_date).days
            # 5% late fee after 30 days
            if days_overdue > 30:
                return self.get_remaining_amount() * Decimal('0.05')
        return Decimal('0.00')


class LoanPayment(models.Model):
    """Loan payment transactions"""
    PAYMENT_METHODS = [
        ('wallet', 'Wallet'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('cash', 'Cash'),
    ]
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    schedule = models.ForeignKey(LoanSchedule, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    
    # Payment details
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    # Transaction tracking
    wallet_transaction = models.ForeignKey('mses.WalletTransaction', on_delete=models.SET_NULL, null=True, blank=True)
    
    payment_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = "Loan Payment"
        verbose_name_plural = "Loan Payments"
    
    def __str__(self):
        return f"Payment {self.id} - {self.loan.id} - {self.amount}"
    
    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Payment amount must be positive")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
        # Update schedule payment
        self.schedule.amount_paid += self.amount
        if self.schedule.amount_paid >= self.schedule.total_due:
            self.schedule.status = 'paid'
        elif self.schedule.amount_paid > 0:
            self.schedule.status = 'partial'
        self.schedule.payment_date = self.payment_date
        self.schedule.save()
        
        # Update loan totals
        self.loan.total_paid += self.amount
        self.loan.outstanding_balance = self.loan.get_remaining_balance()
        self.loan.save()


class LoanDocument(models.Model):
    """Documents related to loan applications and loans"""
    DOCUMENT_TYPES = [
        ('business_plan', 'Business Plan'),
        ('financial_statement', 'Financial Statement'),
        ('bank_statement', 'Bank Statement'),
        ('id_document', 'ID Document'),
        ('collateral_document', 'Collateral Document'),
        ('other', 'Other'),
    ]
    
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='loan_documents/')
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Loan Document"
        verbose_name_plural = "Loan Documents"
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.filename}"
