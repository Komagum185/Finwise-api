from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid
from django.utils import timezone

User = get_user_model()


class SalesData(models.Model):
    """Sales data model for tracking daily sales performance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_data')
    date = models.DateField()
    revenue = models.DecimalField(max_digits=15, decimal_places=2)
    orders = models.IntegerField(validators=[MinValueValidator(0)])
    customers = models.IntegerField(validators=[MinValueValidator(0)])
    average_order_value = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Sales Data"
        verbose_name_plural = "Sales Data"
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.revenue}"
    
    def clean(self):
        if self.revenue < 0:
            raise ValidationError("Revenue cannot be negative")
        if self.orders < 0:
            raise ValidationError("Orders cannot be negative")
        if self.customers < 0:
            raise ValidationError("Customers cannot be negative")
        if self.average_order_value < 0:
            raise ValidationError("Average order value cannot be negative")
        
        # Validate average order value calculation
        if self.orders > 0 and self.revenue > 0:
            calculated_aov = self.revenue / self.orders
            if abs(calculated_aov - self.average_order_value) > 0.01:
                raise ValidationError("Average order value does not match revenue/orders")
    
    def save(self, *args, **kwargs):
        self.clean()
        # Calculate average order value if not set
        if self.orders > 0 and not self.average_order_value:
            self.average_order_value = self.revenue / self.orders
        super().save(*args, **kwargs)
    
    def get_growth_rate(self, previous_date):
        """Calculate growth rate compared to a previous date"""
        try:
            previous_data = SalesData.objects.get(user=self.user, date=previous_date)
            if previous_data.revenue > 0:
                return ((self.revenue - previous_data.revenue) / previous_data.revenue) * 100
            return 0
        except SalesData.DoesNotExist:
            return 0
    
    def get_customer_retention_rate(self, previous_date):
        """Calculate customer retention rate"""
        try:
            previous_data = SalesData.objects.get(user=self.user, date=previous_date)
            if previous_data.customers > 0:
                return (self.customers / previous_data.customers) * 100
            return 0
        except SalesData.DoesNotExist:
            return 0


class ProductPerformance(models.Model):
    """Product performance tracking model"""
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_performance')
    product_name = models.CharField(max_length=255)
    sales = models.IntegerField(validators=[MinValueValidator(0)])
    revenue = models.DecimalField(max_digits=15, decimal_places=2)
    growth = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=100, blank=True)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='monthly')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Product Performance"
        verbose_name_plural = "Product Performance"
        indexes = [
            models.Index(fields=['user', 'product_name']),
            models.Index(fields=['category']),
            models.Index(fields=['period']),
        ]
    
    def __str__(self):
        return f"{self.product_name} - {self.revenue} ({self.period})"
    
    def clean(self):
        if self.sales < 0:
            raise ValidationError("Sales cannot be negative")
        if self.revenue < 0:
            raise ValidationError("Revenue cannot be negative")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def calculate_growth(self, previous_period_data):
        """Calculate growth rate compared to previous period"""
        if previous_period_data and previous_period_data.revenue > 0:
            self.growth = ((self.revenue - previous_period_data.revenue) / previous_period_data.revenue) * 100
            self.save()
    
    def get_performance_score(self):
        """Calculate performance score based on sales and growth"""
        base_score = min(self.sales * 10, 100)  # Base score from sales volume
        growth_bonus = max(self.growth or 0, 0)  # Bonus from positive growth
        return min(base_score + growth_bonus, 100)


class MarketTrends(models.Model):
    """Market trends and insights model"""
    IMPACT_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trend = models.CharField(max_length=255)
    impact = models.CharField(max_length=20, choices=IMPACT_CHOICES)
    description = models.TextField(blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, 
                                   validators=[MinValueValidator(0), MaxValueValidator(100)])
    region = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Market Trend"
        verbose_name_plural = "Market Trends"
        indexes = [
            models.Index(fields=['impact']),
            models.Index(fields=['region']),
            models.Index(fields=['confidence']),
        ]
    
    def __str__(self):
        return f"{self.trend} - {self.get_impact_display()}"
    
    def clean(self):
        if self.confidence < 0 or self.confidence > 100:
            raise ValidationError("Confidence must be between 0 and 100")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def get_impact_score(self):
        """Calculate impact score based on confidence and impact type"""
        base_score = self.confidence
        if self.impact == 'positive':
            return base_score
        elif self.impact == 'negative':
            return -base_score
        else:
            return 0
    
    def is_high_confidence(self):
        """Check if trend has high confidence (>80%)"""
        return self.confidence >= 80
    
    def is_critical_trend(self):
        """Check if trend is critical (high confidence + significant impact)"""
        return self.confidence >= 90 and self.impact != 'neutral'


class Predictions(models.Model):
    """Business predictions and forecasting model"""
    TREND_CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
        ('stable', 'Stable'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    metric = models.CharField(max_length=100)
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    predicted_value = models.DecimalField(max_digits=15, decimal_places=2)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, 
                                   validators=[MinValueValidator(0), MaxValueValidator(100)])
    trend = models.CharField(max_length=20, choices=TREND_CHOICES)
    prediction_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-prediction_date', '-created_at']
        verbose_name = "Prediction"
        verbose_name_plural = "Predictions"
        indexes = [
            models.Index(fields=['user', 'metric']),
            models.Index(fields=['prediction_date']),
            models.Index(fields=['trend']),
        ]
    
    def __str__(self):
        return f"{self.metric} - {self.get_trend_display()} ({self.confidence}%)"
    
    def clean(self):
        if self.current_value < 0:
            raise ValidationError("Current value cannot be negative")
        if self.predicted_value < 0:
            raise ValidationError("Predicted value cannot be negative")
        if self.confidence < 0 or self.confidence > 100:
            raise ValidationError("Confidence must be between 0 and 100")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def get_prediction_accuracy(self, actual_value):
        """Calculate prediction accuracy when actual value is known"""
        if self.predicted_value > 0:
            error_percentage = abs(actual_value - self.predicted_value) / self.predicted_value * 100
            return max(100 - error_percentage, 0)
        return 0
    
    def get_change_percentage(self):
        """Calculate percentage change from current to predicted value"""
        if self.current_value > 0:
            return ((self.predicted_value - self.current_value) / self.current_value) * 100
        return 0
    
    def is_high_confidence_prediction(self):
        """Check if prediction has high confidence (>85%)"""
        return self.confidence >= 85
    
    def get_prediction_category(self):
        """Get prediction category based on confidence and trend"""
        if self.confidence >= 90:
            return 'high_confidence'
        elif self.confidence >= 70:
            return 'medium_confidence'
        else:
            return 'low_confidence'
