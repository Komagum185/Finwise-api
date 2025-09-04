from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('agent', 'Agent'),
        ('mse', 'MSE'),
        ('partner', 'Partner'),
    ]
    
    RIGHTS_CHOICES = [
        ('viewer', 'Viewer'),
        ('editor', 'Editor'),
        ('export', 'Export'),
        ('admin', 'Admin'),
    ]
    
    # Basic fields
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=20, unique=True)
    NIN = models.CharField(max_length=20, unique=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Role and permissions
    role = models.CharField(max_length=15, choices=ROLE_CHOICES)
    rights = models.CharField(max_length=10, choices=RIGHTS_CHOICES, null=True, blank=True)
    
    # Status fields
    is_approved = models.BooleanField(default=False)
    first_login = models.BooleanField(default=True)
    
    # Additional fields for role-based functionality (commented out until migrations are run)
    # mse_name = models.CharField(max_length=100, blank=True, null=True, help_text="MSE name if user is MSE")
    # assigned_agent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
    #                                  related_name='assigned_mse_users', help_text="Agent assigned to this MSE/Partner")
    # partner_institution = models.CharField(max_length=100, blank=True, null=True, 
    #                                      help_text="Institution name if user is Partner")
    
    # Timestamps (commented out until migrations are run)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number', 'NIN']

    class Meta:
        db_table = 'authentication_customuser'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def clean(self):
        """Validate role-specific requirements"""
        # Temporarily disabled until new fields are added
        # if self.role == 'mse' and not self.mse_name:
        #     raise ValidationError("MSE users must have an MSE name")
        
        # if self.role == 'partner' and not self.partner_institution:
        #     raise ValidationError("Partner users must have an institution name")
        pass
    
    def save(self, *args, **kwargs):
        # Set default rights based on role
        if not self.rights:
            if self.role == 'super_admin':
                self.rights = 'admin'
            elif self.role == 'agent':
                self.rights = 'editor'
            elif self.role == 'mse':
                self.rights = 'viewer'
            elif self.role == 'partner':
                self.rights = 'viewer'
        
        # Auto-approve super admin users
        if self.role == 'super_admin':
            self.is_approved = True
        
        super().save(*args, **kwargs)
    
    @property
    def is_super_admin(self):
        return self.role == 'super_admin' and self.is_superuser
    
    @property
    def is_agent(self):
        return self.role == 'agent'
    
    @property
    def is_mse(self):
        return self.role == 'mse'
    
    @property
    def is_partner(self):
        return self.role == 'partner'
    
    @property
    def can_manage_users(self):
        return self.role == 'super_admin'
    
    @property
    def can_manage_mse(self):
        return self.role in ['super_admin', 'agent']
    
    @property
    def can_view_reports(self):
        return self.role in ['super_admin', 'agent', 'mse', 'partner']
    
    @property
    def can_export_data(self):
        return self.rights in ['export', 'admin']
    
    def get_assigned_users(self):
        """Get users assigned to this agent"""
        if self.role == 'agent':
            return CustomUser.objects.filter(assigned_agent=self)
        return CustomUser.objects.none()
