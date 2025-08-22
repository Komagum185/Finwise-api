from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import timedelta

from .models import (
    Product, MarketOpportunity, OpportunityApplication, 
    MarketplaceMessage, ProductReview, MarketplaceNotification
)
from .serializers import (
    ProductSerializer, ProductCreateSerializer,
    MarketOpportunitySerializer, MarketOpportunityCreateSerializer,
    OpportunityApplicationSerializer, OpportunityApplicationCreateSerializer,
    MarketplaceMessageSerializer, MarketplaceMessageCreateSerializer,
    ProductReviewSerializer, ProductReviewCreateSerializer,
    MarketplaceNotificationSerializer, ProductSearchSerializer,
    MarketplaceStatisticsSerializer
)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProductCreateSerializer
        return ProductSerializer
    
    def get_queryset(self):
        """Filter products based on user permissions"""
        queryset = super().get_queryset()
        
        # If user is not staff, only show available products
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='available')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_products(self, request):
        """Get current user's products"""
        products = self.queryset.filter(seller=request.user)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Search products with filters"""
        serializer = ProductSearchSerializer(data=request.data)
        if serializer.is_valid():
            queryset = self.get_queryset()
            
            # Apply search filters
            query = serializer.validated_data.get('query')
            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query) | 
                    Q(description__icontains=query) |
                    Q(category__icontains=query)
                )
            
            category = serializer.validated_data.get('category')
            if category:
                queryset = queryset.filter(category=category)
            
            min_price = serializer.validated_data.get('min_price')
            if min_price:
                queryset = queryset.filter(price__gte=min_price)
            
            max_price = serializer.validated_data.get('max_price')
            if max_price:
                queryset = queryset.filter(price__lte=max_price)
            
            is_organic = serializer.validated_data.get('is_organic')
            if is_organic is not None:
                queryset = queryset.filter(is_organic=is_organic)
            
            quality_grade = serializer.validated_data.get('quality_grade')
            if quality_grade:
                queryset = queryset.filter(quality_grade=quality_grade)
            
            # Apply sorting
            sort_by = serializer.validated_data.get('sort_by', 'created_at')
            sort_order = serializer.validated_data.get('sort_order', 'desc')
            
            if sort_order == 'desc':
                sort_by = f'-{sort_by}'
            
            queryset = queryset.order_by(sort_by)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """Update product stock"""
        product = self.get_object()
        
        # Check if user owns the product
        if product.seller != request.user:
            return Response(
                {'error': 'You can only update your own products'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_stock = request.data.get('stock')
        if new_stock is None:
            return Response(
                {'error': 'Stock value is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_stock = int(new_stock)
            if new_stock < 0:
                raise ValueError("Stock cannot be negative")
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product.stock = new_stock
        product.update_stock_status()
        
        serializer = self.get_serializer(product)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_price(self, request, pk=None):
        """Update product price"""
        product = self.get_object()
        
        # Check if user owns the product
        if product.seller != request.user:
            return Response(
                {'error': 'You can only update your own products'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_price = request.data.get('price')
        if new_price is None:
            return Response(
                {'error': 'Price value is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_price = float(new_price)
            if new_price < 0:
                raise ValueError("Price cannot be negative")
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product.price = new_price
        product.save()
        
        serializer = self.get_serializer(product)
        return Response(serializer.data)


class MarketOpportunityViewSet(viewsets.ModelViewSet):
    """ViewSet for MarketOpportunity"""
    queryset = MarketOpportunity.objects.all()
    serializer_class = MarketOpportunitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MarketOpportunityCreateSerializer
        return MarketOpportunitySerializer
    
    def get_queryset(self):
        """Filter opportunities based on user permissions"""
        queryset = super().get_queryset()
        
        # If user is not staff, only show open opportunities
        if not self.request.user.is_staff:
            queryset = queryset.filter(status='open')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_opportunities(self, request):
        """Get current user's created opportunities"""
        opportunities = self.queryset.filter(creator=request.user)
        serializer = self.get_serializer(opportunities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def open_opportunities(self, request):
        """Get open opportunities"""
        opportunities = self.queryset.filter(status='open')
        serializer = self.get_serializer(opportunities, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def close_opportunity(self, request, pk=None):
        """Close an opportunity"""
        opportunity = self.get_object()
        
        # Check if user owns the opportunity
        if opportunity.creator != request.user:
            return Response(
                {'error': 'You can only close your own opportunities'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        opportunity.status = 'closed'
        opportunity.save()
        
        serializer = self.get_serializer(opportunity)
        return Response(serializer.data)


class OpportunityApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for OpportunityApplication"""
    serializer_class = OpportunityApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OpportunityApplicationCreateSerializer
        return OpportunityApplicationSerializer
    
    def get_queryset(self):
        """Filter applications based on user permissions"""
        user = self.request.user
        
        if user.is_staff:
            # Staff can see all applications
            return OpportunityApplication.objects.all()
        else:
            # Users can only see their own applications
            return OpportunityApplication.objects.filter(applicant=user)
    
    @action(detail=False, methods=['get'])
    def my_applications(self, request):
        """Get current user's applications"""
        applications = self.get_queryset().filter(applicant=request.user)
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def review_application(self, request, pk=None):
        """Review an application (staff only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can review applications'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        application = self.get_object()
        new_status = request.data.get('status')
        review_notes = request.data.get('review_notes', '')
        
        if not new_status:
            return Response(
                {'error': 'Status is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in dict(OpportunityApplication.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.status = new_status
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.review_notes = review_notes
        application.save()
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)


class MarketplaceMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for MarketplaceMessage"""
    serializer_class = MarketplaceMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MarketplaceMessageCreateSerializer
        return MarketplaceMessageSerializer
    
    def get_queryset(self):
        """Filter messages based on user"""
        user = self.request.user
        return MarketplaceMessage.objects.filter(
            Q(sender=user) | Q(recipient=user)
        )
    
    @action(detail=False, methods=['get'])
    def inbox(self, request):
        """Get received messages"""
        messages = self.get_queryset().filter(recipient=request.user)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Get sent messages"""
        messages = self.get_queryset().filter(sender=request.user)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()
        
        # Check if user is the recipient
        if message.recipient != request.user:
            return Response(
                {'error': 'You can only mark your own messages as read'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.mark_as_read()
        serializer = self.get_serializer(message)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all messages as read"""
        messages = self.get_queryset().filter(
            recipient=request.user,
            is_read=False
        )
        
        for message in messages:
            message.mark_as_read()
        
        return Response({'message': f'Marked {messages.count()} messages as read'})


class ProductReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for ProductReview"""
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProductReviewCreateSerializer
        return ProductReviewSerializer
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get current user's reviews"""
        reviews = self.queryset.filter(reviewer=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def product_reviews(self, request):
        """Get reviews for a specific product"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reviews = self.queryset.filter(product_id=product_id)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)


class MarketplaceNotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for MarketplaceNotification"""
    serializer_class = MarketplaceNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter notifications for current user"""
        return MarketplaceNotification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        notifications = self.get_queryset().filter(is_read=False)
        
        for notification in notifications:
            notification.mark_as_read()
        
        return Response({'message': f'Marked {notifications.count()} notifications as read'})


class MarketplaceStatisticsViewSet(viewsets.ViewSet):
    """ViewSet for marketplace statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get marketplace overview statistics"""
        # Get date range from query params
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Calculate statistics
        total_products = Product.objects.filter(created_at__gte=start_date).count()
        total_opportunities = MarketOpportunity.objects.filter(created_at__gte=start_date).count()
        total_messages = MarketplaceMessage.objects.filter(created_at__gte=start_date).count()
        total_reviews = ProductReview.objects.filter(created_at__gte=start_date).count()
        
        # Active sellers (users who have listed products)
        active_sellers = User.objects.filter(
            products__created_at__gte=start_date
        ).distinct().count()
        
        # Average product rating
        avg_rating = ProductReview.objects.aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0
        
        stats = {
            'total_products': total_products,
            'total_opportunities': total_opportunities,
            'total_messages': total_messages,
            'total_reviews': total_reviews,
            'active_sellers': active_sellers,
            'average_product_rating': round(avg_rating, 1),
            'period': f'Last {days} days'
        }
        
        serializer = MarketplaceStatisticsSerializer(stats)
        return Response(serializer.data)
