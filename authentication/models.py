from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('mse', 'MSE'),
        ('partner', 'Partner'),
    ]
    
    RIGHTS_CHOICES = [
        ('viewer', 'Viewer'),
        ('export', 'Export'),
    ]
    
    first_name = models.CharField(max_length=50, blank=True)  # added
    last_name = models.CharField(max_length=50, blank=True)  
    phone_number = models.CharField(max_length=20, unique=True)
    NIN = models.CharField(max_length=20, unique=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    rights = models.CharField(max_length=10, choices=RIGHTS_CHOICES, null=True, blank=True)
    is_approved = models.BooleanField(default=False)  # Admin approval
    first_login = models.BooleanField(default=True)   # True until password is changed first time

    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number', 'NIN']

    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def save(self, *args, **kwargs):
        # Set default rights for partner users
        if self.role == 'partner' and not self.rights:
            self.rights = 'viewer'
        super().save(*args, **kwargs)
