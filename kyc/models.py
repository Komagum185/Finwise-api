from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import uuid
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class KYCDocument(models.Model):
    """KYC document model for user verification"""
    DOCUMENT_TYPES = [
        ('national_id', 'National ID'),
        ('passport', 'Passport'),
        ('drivers_license', 'Driver\'s License'),
        ('business_license', 'Business License'),
        ('tax_certificate', 'Tax Certificate'),
        ('bank_statement', 'Bank Statement'),
        ('utility_bill', 'Utility Bill'),
        ('other', 'Other'),
    ]
    
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kyc_documents')
    
    # Document details
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=100, blank=True)
    issuing_country = models.CharField(max_length=100, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # File upload
    file = models.FileField(upload_to='kyc_documents/')
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=50, blank=True)
    
    # Verification
    status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "KYC Document"
        verbose_name_plural = "KYC Documents"
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.user.username} - {self.status}"
    
    def clean(self):
        if self.expiry_date and self.issue_date and self.expiry_date <= self.issue_date:
            raise ValidationError("Expiry date must be after issue date")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if document is expired"""
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False
    
    def get_file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)


class BankAccount(models.Model):
    """Bank account model for KYC verification"""
    ACCOUNT_TYPES = [
        ('savings', 'Savings Account'),
        ('current', 'Current Account'),
        ('business', 'Business Account'),
        ('joint', 'Joint Account'),
    ]
    
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_accounts')
    
    # Bank details
    bank_name = models.CharField(max_length=200)
    branch_name = models.CharField(max_length=200, blank=True)
    account_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    account_holder_name = models.CharField(max_length=200)
    
    # Account details
    currency = models.CharField(max_length=3, default='UGX')
    is_active = models.BooleanField(default=True)
    
    # Verification
    status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_bank_accounts')
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"
        unique_together = ['user', 'bank_name', 'account_number']
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_number} - {self.user.username}"
    
    def clean(self):
        if not self.bank_name:
            raise ValidationError("Bank name is required")
        if not self.account_number:
            raise ValidationError("Account number is required")
        if not self.account_holder_name:
            raise ValidationError("Account holder name is required")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class MobileMoneyAccount(models.Model):
    """Mobile money account model for KYC verification"""
    PROVIDER_CHOICES = [
        ('mtn', 'MTN Mobile Money'),
        ('airtel', 'Airtel Money'),
        ('mpesa', 'M-Pesa'),
        ('other', 'Other'),
    ]
    
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mobile_money_accounts')
    
    # Account details
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    phone_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Verification
    status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_mobile_accounts')
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Mobile Money Account"
        verbose_name_plural = "Mobile Money Accounts"
        unique_together = ['user', 'provider', 'phone_number']
    
    def __str__(self):
        return f"{self.get_provider_display()} - {self.phone_number} - {self.user.username}"
    
    def clean(self):
        if not self.provider:
            raise ValidationError("Provider is required")
        if not self.phone_number:
            raise ValidationError("Phone number is required")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class KYCVerification(models.Model):
    """Overall KYC verification status for users"""
    VERIFICATION_LEVELS = [
        ('basic', 'Basic Verification'),
        ('enhanced', 'Enhanced Verification'),
        ('full', 'Full Verification'),
    ]
    
    VERIFICATION_STATUS = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kyc_verification')
    
    # Verification details
    verification_level = models.CharField(max_length=20, choices=VERIFICATION_LEVELS, default='basic')
    status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='not_started')
    
    # Progress tracking
    documents_uploaded = models.IntegerField(default=0)
    documents_verified = models.IntegerField(default=0)
    bank_accounts_verified = models.IntegerField(default=0)
    mobile_accounts_verified = models.IntegerField(default=0)
    
    # Verification details
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_kyc')
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    # Requirements
    required_documents = models.JSONField(default=list, help_text="List of required document types")
    required_bank_accounts = models.BooleanField(default=False)
    required_mobile_accounts = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "KYC Verification"
        verbose_name_plural = "KYC Verifications"
    
    def __str__(self):
        return f"KYC Verification - {self.user.username} - {self.status}"
    
    def get_verification_progress(self):
        """Calculate verification progress percentage"""
        total_requirements = 0
        completed_requirements = 0
        
        # Count document requirements
        total_requirements += len(self.required_documents)
        completed_requirements += self.documents_verified
        
        # Count account requirements
        if self.required_bank_accounts:
            total_requirements += 1
            if self.bank_accounts_verified > 0:
                completed_requirements += 1
        
        if self.required_mobile_accounts:
            total_requirements += 1
            if self.mobile_accounts_verified > 0:
                completed_requirements += 1
        
        if total_requirements == 0:
            return 0
        
        return round((completed_requirements / total_requirements) * 100, 2)
    
    def is_fully_verified(self):
        """Check if user is fully verified"""
        return self.status == 'approved' and self.get_verification_progress() == 100
    
    def update_verification_status(self):
        """Update verification status based on progress"""
        progress = self.get_verification_progress()
        
        if progress == 0:
            self.status = 'not_started'
        elif progress < 100:
            self.status = 'in_progress'
        elif progress == 100 and self.status != 'approved':
            self.status = 'pending_review'
        
        self.save()


class VerificationRequest(models.Model):
    """Verification requests for manual review"""
    REQUEST_TYPES = [
        ('document', 'Document Verification'),
        ('bank_account', 'Bank Account Verification'),
        ('mobile_account', 'Mobile Money Verification'),
        ('kyc_review', 'KYC Review'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verification_requests')
    
    # Request details
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Related objects
    document = models.ForeignKey(KYCDocument, on_delete=models.CASCADE, null=True, blank=True)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, null=True, blank=True)
    mobile_account = models.ForeignKey(MobileMoneyAccount, on_delete=models.CASCADE, null=True, blank=True)
    kyc_verification = models.ForeignKey(KYCVerification, on_delete=models.CASCADE, null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    
    # Review details
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Verification Request"
        verbose_name_plural = "Verification Requests"
    
    def __str__(self):
        return f"{self.get_request_type_display()} - {self.user.username} - {self.status}"
