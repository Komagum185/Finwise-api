from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
import uuid
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    """Custom user model with additional fields"""
    
    # Additional fields
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    # Financial preferences
    default_currency = models.CharField(max_length=3, default='UGX')
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def __str__(self):
        return self.username
    
    @property
    def full_name(self):
        """Return the full name of the user"""
        return f"{self.first_name} {self.last_name}".strip() or self.username


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
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_registrations'
    )
    rejection_reason = models.TextField(blank=True)
    
    # OTP verification
    otp_code = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.username} - {self.status}"
    
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


class OTPVerification(models.Model):
    """Model for OTP verification for existing users"""
    PURPOSE_CHOICES = [
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
        ('phone_verification', 'Phone Verification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otp_verifications')
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
        return not self.is_used and not self.is_expired
    
    def mark_as_used(self):
        """Mark OTP as used"""
        self.is_used = True
        self.save()
    
    @classmethod
    def create_otp(cls, user, purpose, expiry_minutes=15):
        """Create a new OTP for user"""
        import random
        otp_code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        
        # Invalidate any existing OTPs for the same user and purpose
        cls.objects.filter(
            user=user, 
            purpose=purpose, 
            is_used=False
        ).update(is_used=True)
        
        return cls.objects.create(
            user=user,
            purpose=purpose,
            otp_code=otp_code,
            expires_at=expires_at
        )
