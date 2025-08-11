from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
import uuid
from django.utils import timezone
from datetime import timedelta


class User(models.Model):
    """User model matching the TypeScript User interface exactly"""
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Input MSE', 'Input MSE'),
        ('Production MSE', 'Production MSE'),
        ('Output MSE', 'Output MSE'),
    ]
    
    # Core user fields matching TypeScript interface
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Full name of the user")
    email = models.EmailField(unique=True, help_text="User's email address")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, help_text="User's role in the system")
    
    # Optional fields from TypeScript interface
    mse_type = models.CharField(max_length=50, blank=True, help_text="Type of MSE if applicable")
    mse_code = models.CharField(max_length=50, blank=True, help_text="MSE code if applicable")
    phone = models.CharField(max_length=20, blank=True, help_text="User's phone number")
    company = models.CharField(max_length=200, blank=True, help_text="User's company name")
    location = models.CharField(max_length=200, blank=True, help_text="User's location")
    
    # Additional metadata
    is_active = models.BooleanField(default=True, help_text="Whether the user account is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.email}) - {self.role}"
    
    @property
    def display_name(self):
        """Return the display name for the user"""
        return self.name or self.email.split('@')[0]


class PendingUser(models.Model):
    """PendingUser model matching the TypeScript PendingUser interface exactly"""
    ROLE_CHOICES = [
        ('Input MSE', 'Input MSE'),
        ('Production MSE', 'Production MSE'),
        ('Output MSE', 'Output MSE'),
    ]
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    
    # Core fields matching TypeScript interface
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Full name of the user")
    email = models.EmailField(unique=True, help_text="User's email address")
    phone = models.CharField(max_length=20, help_text="User's phone number")
    company = models.CharField(max_length=200, help_text="User's company name")
    mse_type = models.CharField(max_length=20, choices=ROLE_CHOICES, help_text="Type of MSE")
    registration_date = models.DateTimeField(auto_now_add=True, help_text="Date of registration")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', help_text="Registration status")
    
    # Additional fields for enhanced registration
    gender = models.CharField(max_length=20, blank=True, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say')
    ])
    branch_id = models.CharField(max_length=100, blank=True, help_text="Branch identifier")
    group_id = models.CharField(max_length=100, blank=True, help_text="Group identifier")
    cause = models.TextField(blank=True, help_text="Reason for registration")
    nationality = models.CharField(max_length=100, blank=True, help_text="User's nationality")
    send_sms = models.BooleanField(default=False, help_text="Whether to send SMS notifications")
    subscribe = models.BooleanField(default=False, help_text="Whether to subscribe to updates")
    company_id = models.CharField(max_length=100, blank=True, help_text="Company identifier")
    
    # Review and approval fields
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        'users.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='auth_reviewed_pending_users'
    )
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection if applicable")
    
    # OTP verification
    otp_code = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_verified = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Pending User"
        verbose_name_plural = "Pending Users"
        ordering = ['-registration_date']
    
    def __str__(self):
        return f"{self.name} ({self.email}) - {self.status}"
    
    @property
    def is_otp_expired(self):
        """Check if OTP has expired (5 minutes)"""
        if not self.otp_created_at:
            return True
        return timezone.now() > self.otp_created_at + timedelta(minutes=5)
    
    def generate_otp(self):
        """Generate a new 6-digit OTP"""
        import random
        self.otp_code = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.otp_verified = False
        self.save()
        return self.otp_code
    
    def verify_otp(self, otp):
        """Verify the provided OTP"""
        if self.otp_code == otp and not self.is_otp_expired:
            self.otp_verified = True
            self.save()
            return True
        return False


class PendingRegistration(models.Model):
    """Model for pending user registrations that need approval"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=17, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    default_currency = models.CharField(max_length=3, default='USD')
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Registration details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        'users.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='auth_reviewed_registrations'
    )
    rejection_reason = models.TextField(blank=True)
    
    # OTP verification
    otp_code = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.username} - {self.email} ({self.status})"
    
    @property
    def is_otp_expired(self):
        """Check if OTP has expired (15 minutes)"""
        if not self.otp_created_at:
            return True
        return timezone.now() > self.otp_created_at + timedelta(minutes=15)
    
    def generate_otp(self):
        """Generate a new 6-digit OTP"""
        import random
        self.otp_code = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.otp_verified = False
        self.save()
        return self.otp_code
    
    def verify_otp(self, otp):
        """Verify the provided OTP"""
        if self.otp_code == otp and not self.is_otp_expired:
            self.otp_verified = True
            self.save()
            return True
        return False


class OTPVerification(models.Model):
    """Model for OTP verification for existing users"""
    PURPOSE_CHOICES = [
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
        ('phone_verification', 'Phone Verification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='auth_otp_verifications')
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.purpose} - {self.otp_code}"
    
    @property
    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if OTP is valid and not used"""
        return not self.is_expired and not self.is_used
    
    def mark_as_used(self):
        """Mark OTP as used"""
        self.is_used = True
        self.save()
    
    @classmethod
    def create_otp(cls, user, purpose, expiry_minutes=15):
        """Create a new OTP for a user"""
        import random
        otp_code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        
        return cls.objects.create(
            user=user,
            purpose=purpose,
            otp_code=otp_code,
            expires_at=expires_at
        )
