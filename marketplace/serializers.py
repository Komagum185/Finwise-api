from rest_framework import serializers
from .models import (
    Product, MarketOpportunity, OpportunityApplication, 
    MarketplaceMessage, ProductReview, MarketplaceNotification
)


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product"""
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    quality_grade_display = serializers.CharField(source='get_quality_grade_display', read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'seller_name', 'name', 'category', 'category_display', 
            'subcategory', 'description', 'price', 'stock', 'unit', 'status', 
            'status_display', 'quality_grade', 'quality_grade_display', 'is_organic',
            'weight', 'dimensions', 'expiry_date', 'batch_number', 'barcode',
            'origin', 'processing_method', 'certifications', 'specifications',
            'images', 'created_at', 'updated_at', 'average_rating', 'review_count'
        ]
        read_only_fields = ['id', 'seller', 'created_at', 'updated_at', 'average_rating', 'review_count']
    
    def get_average_rating(self, obj):
        """Calculate average rating for the product"""
        reviews = obj.reviews.all()
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            return round(total_rating / len(reviews), 1)
        return 0
    
    def get_review_count(self, obj):
        """Get number of reviews for the product"""
        return obj.reviews.count()


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Product"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'subcategory', 'description', 'price', 'stock', 'unit',
            'quality_grade', 'is_organic', 'weight', 'dimensions', 'expiry_date',
            'batch_number', 'barcode', 'origin', 'processing_method', 'certifications',
            'specifications', 'images'
        ]
    
    def create(self, validated_data):
        validated_data['seller'] = self.context['request'].user
        return super().create(validated_data)


class MarketOpportunitySerializer(serializers.ModelSerializer):
    """Serializer for MarketOpportunity"""
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    opportunity_type_display = serializers.CharField(source='get_opportunity_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.SerializerMethodField()
    application_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MarketOpportunity
        fields = [
            'id', 'creator', 'creator_name', 'title', 'description', 'opportunity_type',
            'opportunity_type_display', 'status', 'status_display', 'required_products',
            'quantity_needed', 'budget_range', 'deadline', 'location', 'contact_person',
            'contact_phone', 'contact_email', 'requirements', 'terms_conditions',
            'created_at', 'updated_at', 'is_expired', 'application_count'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at', 'is_expired', 'application_count']
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_application_count(self, obj):
        return obj.applications.count()


class MarketOpportunityCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating MarketOpportunity"""
    
    class Meta:
        model = MarketOpportunity
        fields = [
            'title', 'description', 'opportunity_type', 'required_products',
            'quantity_needed', 'budget_range', 'deadline', 'location', 'contact_person',
            'contact_phone', 'contact_email', 'requirements', 'terms_conditions'
        ]
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)


class OpportunityApplicationSerializer(serializers.ModelSerializer):
    """Serializer for OpportunityApplication"""
    applicant_name = serializers.CharField(source='applicant.username', read_only=True)
    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)
    
    class Meta:
        model = OpportunityApplication
        fields = [
            'id', 'opportunity', 'opportunity_title', 'applicant', 'applicant_name',
            'proposal', 'proposed_price', 'delivery_time', 'status', 'status_display',
            'reviewed_by', 'reviewed_by_name', 'reviewed_at', 'review_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'applicant', 'status', 'reviewed_by', 'reviewed_at', 
            'created_at', 'updated_at'
        ]


class OpportunityApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating OpportunityApplication"""
    
    class Meta:
        model = OpportunityApplication
        fields = ['opportunity', 'proposal', 'proposed_price', 'delivery_time']
    
    def create(self, validated_data):
        validated_data['applicant'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, attrs):
        """Validate application data"""
        opportunity = attrs['opportunity']
        
        # Check if opportunity is still open
        if opportunity.status != 'open':
            raise serializers.ValidationError("This opportunity is no longer accepting applications")
        
        # Check if opportunity has expired
        if opportunity.is_expired():
            raise serializers.ValidationError("This opportunity has expired")
        
        # Check if user has already applied
        if OpportunityApplication.objects.filter(
            opportunity=opportunity,
            applicant=self.context['request'].user
        ).exists():
            raise serializers.ValidationError("You have already applied for this opportunity")
        
        return attrs


class MarketplaceMessageSerializer(serializers.ModelSerializer):
    """Serializer for MarketplaceMessage"""
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    recipient_name = serializers.CharField(source='recipient.username', read_only=True)
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True)
    
    class Meta:
        model = MarketplaceMessage
        fields = [
            'id', 'sender', 'sender_name', 'recipient', 'recipient_name', 'subject',
            'message', 'message_type', 'message_type_display', 'product', 'product_name',
            'opportunity', 'opportunity_title', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'is_read', 'read_at', 'created_at']


class MarketplaceMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating MarketplaceMessage"""
    
    class Meta:
        model = MarketplaceMessage
        fields = ['recipient', 'subject', 'message', 'message_type', 'product', 'opportunity']
    
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for ProductReview"""
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'product', 'product_name', 'reviewer', 'reviewer_name',
            'rating', 'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reviewer', 'created_at', 'updated_at']


class ProductReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ProductReview"""
    
    class Meta:
        model = ProductReview
        fields = ['product', 'rating', 'comment']
    
    def create(self, validated_data):
        validated_data['reviewer'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, attrs):
        """Validate review data"""
        product = attrs['product']
        reviewer = self.context['request'].user
        
        # Check if user has already reviewed this product
        if ProductReview.objects.filter(product=product, reviewer=reviewer).exists():
            raise serializers.ValidationError("You have already reviewed this product")
        
        return attrs


class MarketplaceNotificationSerializer(serializers.ModelSerializer):
    """Serializer for MarketplaceNotification"""
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True)
    
    class Meta:
        model = MarketplaceNotification
        fields = [
            'id', 'user', 'notification_type', 'notification_type_display', 'title',
            'message', 'product', 'product_name', 'opportunity', 'opportunity_title',
            'message_obj', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'is_read', 'read_at', 'created_at']


class ProductSearchSerializer(serializers.Serializer):
    """Serializer for product search"""
    query = serializers.CharField(required=False)
    category = serializers.CharField(required=False)
    min_price = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    is_organic = serializers.BooleanField(required=False)
    quality_grade = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    sort_by = serializers.CharField(required=False, default='created_at')
    sort_order = serializers.CharField(required=False, default='desc')


class MarketplaceStatisticsSerializer(serializers.Serializer):
    """Serializer for marketplace statistics"""
    total_products = serializers.IntegerField()
    total_opportunities = serializers.IntegerField()
    total_messages = serializers.IntegerField()
    total_reviews = serializers.IntegerField()
    active_sellers = serializers.IntegerField()
    average_product_rating = serializers.FloatField()
    period = serializers.CharField()
