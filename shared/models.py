from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from mses.models import MSE


class ValueChain(models.Model):
    """Value Chain model for managing business value chains"""
    VALUE_CHAIN_TYPES = [
        ('input', 'Input'),
        ('production', 'Production'),
        ('output', 'Output'),
        ('integrated', 'Integrated'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('planning', 'Planning'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    value_chain_type = models.CharField(max_length=20, choices=VALUE_CHAIN_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Value Chain"
        verbose_name_plural = "Value Chains"
    
    def __str__(self):
        return f"{self.name} ({self.get_value_chain_type_display()})"


class ValueChainStage(models.Model):
    """Value Chain Stage model for managing stages within a value chain"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
    ]
    
    value_chain = models.ForeignKey(ValueChain, on_delete=models.CASCADE, related_name='stages')
    name = models.CharField(max_length=200)
    description = models.TextField()
    order = models.IntegerField()
    estimated_duration = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    participants = models.JSONField(default=list, help_text="List of participant IDs")
    products = models.JSONField(default=list, help_text="List of product IDs")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Value Chain Stage"
        verbose_name_plural = "Value Chain Stages"
    
    def __str__(self):
        return f"{self.value_chain.name} - Stage {self.order}: {self.name}"

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

    class Meta:
        abstract = True 
        
class ServiceRequest(models.Model):
    """Service Request model for managing service requests"""
    REQUEST_TYPES = [
        ('product_supply', 'Product Supply'),
        ('technical_support', 'Technical Support'),
        ('training', 'Training'),
        ('consultation', 'Consultation'),
        ('maintenance', 'Maintenance'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    supplier = models.CharField(max_length=200)
    supplier_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    requested_by = models.CharField(max_length=200)
    requested_date = models.DateTimeField(auto_now_add=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)
    actual_completion = models.DateTimeField(null=True, blank=True)
    cost = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-requested_date']
        verbose_name = "Service Request"
        verbose_name_plural = "Service Requests"
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.supplier}"


class Notification(models.Model):
    """Notification model for system notifications"""
    NOTIFICATION_TYPES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
        ('alert', 'Alert'),
    ]
    
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    CATEGORY_CHOICES = [
        ('market', 'Market'),
        ('transaction', 'Transaction'),
        ('system', 'System'),
        ('alert', 'Alert'),
        ('report', 'Report'),
    ]
    
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    recipient = models.CharField(max_length=200)
    recipient_id = models.CharField(max_length=100)
    sender = models.CharField(max_length=200)
    sender_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unread')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    action_required = models.BooleanField(default=False)
    action_url = models.URLField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
    
    def __str__(self):
        return f"{self.title} - {self.recipient}"


class StockItem(models.Model):
    """Stock Item model for inventory management"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('expired', 'Expired'),
    ]
    
    mse = models.ForeignKey(MSE, on_delete=models.CASCADE, related_name='stock_items')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=20, default='piece')
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    supplier = models.CharField(max_length=200)
    supplier_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    minimum_stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reorder_point = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cost = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    markup = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Stock Item"
        verbose_name_plural = "Stock Items"
    
    def __str__(self):
        return f"{self.name} - {self.quantity} {self.unit}"
    
    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Quantity cannot be negative")
        if self.price < 0:
            raise ValidationError("Price cannot be negative")
    
    def save(self, *args, **kwargs):
        self.clean()
        # Update status based on quantity
        if self.quantity <= 0:
            self.status = 'out_of_stock'
        elif self.quantity <= self.reorder_point:
            self.status = 'low_stock'
        else:
            self.status = 'available'
        super().save(*args, **kwargs)


class PurchaseOrder(models.Model):
    """Purchase Order model for managing purchase orders"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    mse = models.ForeignKey(MSE, on_delete=models.CASCADE, related_name='purchase_orders')
    supplier_id = models.CharField(max_length=100)
    supplier_name = models.CharField(max_length=200)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery = models.DateTimeField()
    actual_delivery = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_purchase_orders')
    payment_terms = models.CharField(max_length=200, blank=True)
    delivery_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-order_date']
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"
    
    def __str__(self):
        return f"PO-{self.id} - {self.supplier_name}"


class PurchaseOrderItem(models.Model):
    """Purchase Order Item model for individual items in purchase orders"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit = models.CharField(max_length=20, default='piece')
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    received_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Purchase Order Item"
        verbose_name_plural = "Purchase Order Items"
    
    def __str__(self):
        return f"{self.product_name} - {self.quantity} {self.unit}"
    
    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        if self.unit_price < 0:
            raise ValidationError("Unit price cannot be negative")
        if self.received_quantity > self.quantity:
            raise ValidationError("Received quantity cannot exceed ordered quantity")
    
    def save(self, *args, **kwargs):
        self.clean()
        # Calculate total price
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class MarketReport(models.Model):
    """Market Report model for generating and managing reports"""
    REPORT_TYPES = [
        ('sales', 'Sales'),
        ('inventory', 'Inventory'),
        ('purchase', 'Purchase'),
        ('customer', 'Customer'),
        ('supplier', 'Supplier'),
        ('performance', 'Performance'),
    ]
    
    STATUS_CHOICES = [
        ('generated', 'Generated'),
        ('processing', 'Processing'),
        ('failed', 'Failed'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    
    mse = models.ForeignKey(MSE, on_delete=models.CASCADE, related_name='market_reports')
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    period = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='pdf')
    download_url = models.URLField(blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = "Market Report"
        verbose_name_plural = "Market Reports"
    
    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()}"


class MarketReportSummary(models.Model):
    """Market Report Summary model for storing report summaries"""
    report = models.OneToOneField(MarketReport, on_delete=models.CASCADE, related_name='summary')
    total_transactions = models.IntegerField(default=0)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    top_products = models.JSONField(default=list, help_text="List of top product IDs")
    top_customers = models.JSONField(default=list, help_text="List of top customer IDs")
    top_suppliers = models.JSONField(default=list, help_text="List of top supplier IDs")
    growth_rate = models.CharField(max_length=50, blank=True)
    period_comparison = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Market Report Summary"
        verbose_name_plural = "Market Report Summaries"
    
    def __str__(self):
        return f"Summary for {self.report.name}"
