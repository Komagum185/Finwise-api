from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('mse', 'MSE'),
    ]
    first_name = models.CharField(max_length=50, blank=True)  # added
    last_name = models.CharField(max_length=50, blank=True)  
    phone_number = models.CharField(max_length=20, unique=True)
    NIN = models.CharField(max_length=20, unique=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_approved = models.BooleanField(default=False)  # Admin approval
    first_login = models.BooleanField(default=True)   # True until password is changed first time

    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number', 'NIN']

    def __str__(self):
        return f"{self.username} ({self.role})"
