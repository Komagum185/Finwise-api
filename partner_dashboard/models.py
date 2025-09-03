from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid


class Beneficiary(models.Model):
    """Model to store beneficiary information for MSEs"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    AGE_GROUP_CHOICES = [
        ('0-35', 'Youth (0-35)'),
        ('35+', 'Adult (35+)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mse = models.ForeignKey('mse.MSE', on_delete=models.CASCADE, related_name='beneficiaries')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age_group = models.CharField(max_length=10, choices=AGE_GROUP_CHOICES)
    is_refugee = models.BooleanField(default=False)
    has_disability = models.BooleanField(default=False)
    region = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    subcounty = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Beneficiaries'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.mse.first_name}"


class DigitalServiceUsage(models.Model):
    """Model to track digital service usage by MSEs"""
    SERVICE_CHOICES = [
        ('mobile_money', 'Mobile Money'),
        ('digital_banking', 'Digital Banking'),
        ('e_commerce', 'E-Commerce'),
        ('digital_marketing', 'Digital Marketing'),
        ('financial_tools', 'Financial Tools'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mse = models.ForeignKey('mse.MSE', on_delete=models.CASCADE, related_name='digital_services')
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    service_name = models.CharField(max_length=200)
    usage_frequency = models.CharField(max_length=50, default='monthly')
    beneficiaries_count = models.PositiveIntegerField(default=1)
    region = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.mse.first_name} - {self.service_name}"


class PartnerDashboard(models.Model):
    """Model to store partner dashboard configuration and access logs"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboard_access')
    last_access = models.DateTimeField(auto_now=True)
    access_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-last_access']
    
    def __str__(self):
        return f"{self.partner.username} - Last access: {self.last_access}"
