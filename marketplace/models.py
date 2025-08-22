from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.utils import timezone

User = get_user_model()


class Product(models.Model):
    """Marketplace Product"""
    CATEGORY_CHOICES = [
        ('seeds', 'Seeds'),
        ('fertilizers', 'Fertilizers'),
        ('pesticides', 'Pesticides'),
        ('tools', 'Tools'),
        ('machinery', 'Machinery'),
        ('raw_materials', 'Raw Materials'),
        ('processed_goods', 'Processed Goods'),
        ('finished_products', 'Finished Products'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('discontinued', 'Discontinued'),
    ]
    
    QUALITY_CHOICES = [
        ('A', 'Grade A'),
        ('B', 'Grade B'),
        ('C', 'Grade C'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketplace_products')
    
    # Product details
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    
    # Pricing and stock
    price = models.DecimalField(max_digits=15, decimal_places=2)
    stock = models.IntegerField(default=0)
    unit = models.CharField(max_length=20, default='kg')  # kg, pieces, liters, etc.
    
    # Product attributes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    quality_grade = models.CharField(max_length=1, choices=QUALITY_CHOICES, default='B')
    is_organic = models.BooleanField(default=False)
    
    # Additional details
    weight = models.CharField(max_length=50, blank=True)
    dimensions = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    barcode = models.CharField(max_length=100, blank=True)
    
    # Origin and processing
    origin = models.CharField(max_length=100, blank=True)
    processing_method = models.CharField(max_length=100, blank=True)
    
    # Certifications and specifications
    certifications = models.JSONField(default=list, blank=True)
    specifications = models.JSONField(default=dict, blank=True)
    
    # Images
    images = models.JSONField(default=list, blank=True)  # List of image URLs
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.seller.username}"
    
    def update_stock_status(self):
        """Update stock status based on current stock"""
        if self.stock <= 0:
            self.status = 'out_of_stock'
        elif self.stock < 10:  # Low stock threshold
            self.status = 'low_stock'
        else:
            self.status = 'available'
        self.save(update_fields=['status'])


class MarketOpportunity(models.Model):
    """Market Opportunity (Tenders, Bulk Buying Requests)"""
    OPPORTUNITY_TYPES = [
        ('tender', 'Tender'),
        ('bulk_purchase', 'Bulk Purchase Request'),
        ('partnership', 'Partnership Opportunity'),
        ('contract', 'Contract Work'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
        ('awarded', 'Awarded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketplace_created_opportunities')
    
    # Opportunity details
    title = models.CharField(max_length=255)
    description = models.TextField()
    opportunity_type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Requirements
    required_products = models.JSONField(default=list, blank=True)  # List of product requirements
    quantity_needed = models.CharField(max_length=100, blank=True)
    budget_range = models.CharField(max_length=100, blank=True)
    
    # Timeline
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Location and contact
    location = models.CharField(max_length=255, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    # Additional details
    requirements = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Market Opportunity"
        verbose_name_plural = "Market Opportunities"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.creator.username}"
    
    def is_expired(self):
        """Check if opportunity has expired"""
        return timezone.now() > self.deadline


class OpportunityApplication(models.Model):
    """Application for Market Opportunity"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('shortlisted', 'Shortlisted'),
        ('awarded', 'Awarded'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opportunity = models.ForeignKey(MarketOpportunity, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketplace_opportunity_applications')
    
    # Application details
    proposal = models.TextField()
    proposed_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    delivery_time = models.CharField(max_length=100, blank=True)
    
    # Status and review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marketplace_reviewed_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Opportunity Application"
        verbose_name_plural = "Opportunity Applications"
        ordering = ['-created_at']
        unique_together = ['opportunity', 'applicant']
    
    def __str__(self):
        return f"{self.opportunity.title} - {self.applicant.username}"


class MarketplaceMessage(models.Model):
    """Message between marketplace participants"""
    MESSAGE_TYPES = [
        ('product_inquiry', 'Product Inquiry'),
        ('opportunity_inquiry', 'Opportunity Inquiry'),
        ('general', 'General'),
        ('support', 'Support'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketplace_sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketplace_received_messages')
    
    # Message details
    subject = models.CharField(max_length=255)
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='general')
    
    # Related objects
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    opportunity = models.ForeignKey(MarketOpportunity, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Marketplace Message"
        verbose_name_plural = "Marketplace Messages"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.sender.username} to {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class ProductReview(models.Model):
    """Product Review/Rating"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketplace_product_reviews')
    
    # Review details
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    comment = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"
        ordering = ['-created_at']
        unique_together = ['product', 'reviewer']
    
    def __str__(self):
        return f"{self.product.name} - {self.reviewer.username} ({self.rating} stars)"


class MarketplaceNotification(models.Model):
    """Marketplace Notifications"""
    NOTIFICATION_TYPES = [
        ('product_listed', 'Product Listed'),
        ('opportunity_posted', 'Opportunity Posted'),
        ('message_received', 'Message Received'),
        ('application_status', 'Application Status Update'),
        ('price_change', 'Price Change'),
        ('stock_update', 'Stock Update'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketplace_notifications')
    
    # Notification details
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Related objects
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    opportunity = models.ForeignKey(MarketOpportunity, on_delete=models.SET_NULL, null=True, blank=True)
    message_obj = models.ForeignKey(MarketplaceMessage, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Marketplace Notification"
        verbose_name_plural = "Marketplace Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
