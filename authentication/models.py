from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class CustomUser(AbstractUser):
    # Remove rigid role choices - users can have multiple capabilities
    CAPABILITY_CHOICES = [
        ('can_manage_users', 'Can Manage Users'),
        ('can_manage_mse', 'Can Manage MSE'),
        ('can_view_reports', 'Can View Reports'),
        ('can_export_data', 'Can Export Data'),
        ('can_approve_loans', 'Can Approve Loans'),
        ('can_manage_wallets', 'Can Manage Wallets'),
        ('can_access_partner_dashboard', 'Can Access Partner Dashboard'),
        ('can_access_admin_dashboard', 'Can Access Admin Dashboard'),
        ('can_access_agent_dashboard', 'Can Access Agent Dashboard'),
        ('can_access_mse_dashboard', 'Can Access MSE Dashboard'),
        # MSE Business Operations
        ('can_manage_products', 'Can Manage Products'),
        ('can_manage_inventory', 'Can Manage Inventory'),
        ('can_manage_customers', 'Can Manage Customers'),
        ('can_manage_suppliers', 'Can Manage Suppliers'),
        ('can_manage_transactions', 'Can Manage Transactions'),
        ('can_view_market_data', 'Can View Market Data'),
        ('can_manage_loans', 'Can Manage Loans'),
        ('can_manage_wallet', 'Can Manage Wallet'),
    ]
    
    # Basic fields
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=20, unique=True)
    NIN = models.CharField(max_length=20, unique=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Flexible role system - users can have multiple roles
    is_super_admin = models.BooleanField(default=False, help_text="Full system access")
    is_agent = models.BooleanField(default=False, help_text="Can manage assigned MSEs")
    is_mse = models.BooleanField(default=False, help_text="Micro/Small Enterprise user")
    is_partner = models.BooleanField(default=False, help_text="Partner institution user")
    
    # Status fields
    is_approved = models.BooleanField(default=False)
    first_login = models.BooleanField(default=True)
    
    # Additional fields for different user types
    mse_name = models.CharField(max_length=100, blank=True, null=True, 
                               help_text="MSE name if user is MSE")
    assigned_agent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='assigned_users', 
                                     help_text="Agent assigned to this user")
    partner_institution = models.CharField(max_length=100, blank=True, null=True, 
                                         help_text="Institution name if user is Partner")
    
    # Capabilities - many-to-many for flexible permissions
    capabilities = models.JSONField(default=list, blank=True, 
                                  help_text="List of user capabilities")

    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number', 'NIN']

    class Meta:
        db_table = 'authentication_customuser'
        ordering = ['-date_joined']

    def __str__(self):
        roles = []
        if self.is_super_admin:
            roles.append('Super Admin')
        if self.is_agent:
            roles.append('Agent')
        if self.is_mse:
            roles.append('MSE')
        if self.is_partner:
            roles.append('Partner')
        
        role_str = ', '.join(roles) if roles else 'User'
        return f"{self.username} ({role_str})"
    
    def clean(self):
        """Validate user configuration"""
        # At least one role must be selected
        if not any([self.is_super_admin, self.is_agent, self.is_mse, self.is_partner]):
            raise ValidationError("User must have at least one role")
        
        # MSE users must have MSE name
        if self.is_mse and not self.mse_name:
            raise ValidationError("MSE users must have an MSE name")
        
        # Partner users must have institution name
        if self.is_partner and not self.partner_institution:
            raise ValidationError("Partner users must have an institution name")
    
    def save(self, *args, **kwargs):
        # Auto-approve super admin users
        if self.is_super_admin:
            self.is_approved = True
            self.is_staff = True
            self.is_superuser = True
        
        # Set default capabilities based on roles
        self._set_default_capabilities()
        
        super().save(*args, **kwargs)
    
    def _set_default_capabilities(self):
        """Set default capabilities based on user roles"""
        capabilities = []
        
        if self.is_super_admin:
            capabilities.extend([
                'can_manage_users',
                'can_manage_mse', 
                'can_view_reports',
                'can_export_data',
                'can_approve_loans',
                'can_manage_wallets',
                'can_access_admin_dashboard',
                'can_access_agent_dashboard',
                'can_access_mse_dashboard',
                'can_access_partner_dashboard',
                # MSE Business Operations (super admin can do everything)
                'can_manage_products',
                'can_manage_inventory',
                'can_manage_customers',
                'can_manage_suppliers',
                'can_manage_transactions',
                'can_view_market_data',
                'can_manage_loans',
                'can_manage_wallet'
            ])
        
        if self.is_agent:
            capabilities.extend([
                'can_manage_mse',
                'can_view_reports',
                'can_export_data',
                'can_approve_loans',
                'can_manage_wallets',
                'can_access_agent_dashboard',
                # Agents can view MSE business data
                'can_view_market_data',
                'can_view_mse_products',
                'can_view_mse_inventory'
            ])
        
        if self.is_mse:
            capabilities.extend([
                'can_view_reports',
                'can_export_data',
                'can_access_mse_dashboard',
                # MSE Business Operations - they can manage their own business
                'can_manage_products',
                'can_manage_inventory',
                'can_manage_customers',
                'can_manage_suppliers',
                'can_manage_transactions',
                'can_view_market_data',
                'can_manage_loans',
                'can_manage_wallet'
            ])
        
        if self.is_partner:
            capabilities.extend([
                'can_view_reports',
                'can_export_data',
                'can_access_partner_dashboard',
                # Partners can view market data and MSE performance
                'can_view_market_data',
                'can_view_mse_products',
                'can_view_mse_inventory'
            ])
        
        # Remove duplicates and set
        self.capabilities = list(set(capabilities))
    
    # Property methods for easy role checking
    @property
    def has_multiple_roles(self):
        """Check if user has multiple roles"""
        return sum([self.is_super_admin, self.is_agent, self.is_mse, self.is_partner]) > 1
    
    @property
    def primary_role(self):
        """Get the primary role (most privileged)"""
        if self.is_super_admin:
            return 'super_admin'
        elif self.is_agent:
            return 'agent'
        elif self.is_mse:
            return 'mse'
        elif self.is_partner:
            return 'partner'
        return 'user'
    
    # Capability checking methods
    def has_capability(self, capability):
        """Check if user has a specific capability"""
        return capability in self.capabilities
    
    def has_any_capability(self, capabilities):
        """Check if user has any of the specified capabilities"""
        return any(cap in self.capabilities for cap in capabilities)
    
    def has_all_capabilities(self, capabilities):
        """Check if user has all of the specified capabilities"""
        return all(cap in self.capabilities for cap in capabilities)
    
    # Role-based access methods
    def can_access_dashboard(self, dashboard_type):
        """Check if user can access a specific dashboard"""
        dashboard_capabilities = {
            'admin': 'can_access_admin_dashboard',
            'agent': 'can_access_agent_dashboard', 
            'mse': 'can_access_mse_dashboard',
            'partner': 'can_access_partner_dashboard'
        }
        
        capability = dashboard_capabilities.get(dashboard_type)
        return capability and self.has_capability(capability)
    
    def get_accessible_dashboards(self):
        """Get list of dashboards user can access"""
        dashboards = []
        if self.can_access_dashboard('admin'):
            dashboards.append('admin')
        if self.can_access_dashboard('agent'):
            dashboards.append('agent')
        if self.can_access_dashboard('mse'):
            dashboards.append('mse')
        if self.can_access_dashboard('partner'):
            dashboards.append('partner')
        return dashboards
    
    # Agent assignment methods
    def get_assigned_users(self):
        """Get users assigned to this agent"""
        if self.is_agent:
            return CustomUser.objects.filter(assigned_agent=self)
        return CustomUser.objects.none()
    
    def get_my_agent(self):
        """Get the agent assigned to this user"""
        return self.assigned_agent
    
    # Business logic methods
    def can_manage_user(self, target_user):
        """Check if this user can manage the target user"""
        # Super admins can manage everyone
        if self.is_super_admin:
            return True
        
        # Agents can manage their assigned users
        if self.is_agent and target_user.assigned_agent == self:
            return True
        
        # Users can manage themselves
        if target_user == self:
            return True
        
        return False
    
    def can_view_mse_data(self, mse_user):
        """Check if this user can view MSE data"""
        # Super admins can view everything
        if self.is_super_admin:
            return True
        
        # Agents can view their assigned MSEs
        if self.is_agent and mse_user.assigned_agent == self:
            return True
        
        # MSEs can view their own data
        if self.is_mse and mse_user == self:
            return True
        
        # Partners can view MSE data (if business logic allows)
        if self.is_partner:
            return True
        
        return False
    
    # MSE Business Operation methods
    def can_manage_own_products(self):
        """Check if user can manage their own products"""
        return self.is_mse and self.has_capability('can_manage_products')
    
    def can_manage_own_inventory(self):
        """Check if user can manage their own inventory"""
        return self.is_mse and self.has_capability('can_manage_inventory')
    
    def can_manage_own_customers(self):
        """Check if user can manage their own customers"""
        return self.is_mse and self.has_capability('can_manage_customers')
    
    def can_manage_own_suppliers(self):
        """Check if user can manage their own suppliers"""
        return self.is_mse and self.has_capability('can_manage_suppliers')
    
    def can_manage_own_transactions(self):
        """Check if user can manage their own transactions"""
        return self.is_mse and self.has_capability('can_manage_transactions')
    
    def can_view_market_data(self):
        """Check if user can view market data"""
        return self.has_capability('can_view_market_data')
    
    def can_manage_own_loans(self):
        """Check if user can manage their own loans"""
        return self.is_mse and self.has_capability('can_manage_loans')
    
    def can_manage_own_wallet(self):
        """Check if user can manage their own wallet"""
        return self.is_mse and self.has_capability('can_manage_wallet')
