from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import MSE, InputMSE, OutputMSE, ProductionMSE, MSECategory, Wallet, UserRole
from .serializers import (
    MSESerializer, InputMSESerializer, OutputMSESerializer, ProductionMSESerializer,
    MSECategorySerializer, WalletSerializer, UserRoleSerializer,
    ComprehensiveMSESerializer, InputMSEListSerializer, OutputMSEListSerializer,
    ProductionMSEListSerializer
)


class MSEViewSet(viewsets.ModelViewSet):
    """ViewSet for MSE model"""
    queryset = MSE.objects.all()
    serializer_class = MSESerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['mse_type', 'status', 'business_type']
    search_fields = ['name', 'registration_number', 'tax_id', 'email']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ComprehensiveMSESerializer
        return MSESerializer

    @action(detail=True, methods=['get'])
    def category_details(self, request, pk=None):
        """Get category-specific details for an MSE"""
        mse = self.get_object()
        try:
            category = mse.category
            if category:
                serializer = MSECategorySerializer(category)
                return Response(serializer.data)
            else:
                return Response(
                    {'message': 'No category assigned to this MSE'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except MSECategory.DoesNotExist:
            return Response(
                {'message': 'No category assigned to this MSE'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get MSEs grouped by category"""
        category_type = request.query_params.get('category', None)
        
        if category_type:
            mses = MSE.objects.filter(category__primary_category=category_type)
        else:
            mses = MSE.objects.all()
        
        serializer = self.get_serializer(mses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def business_analytics(self, request):
        """Get comprehensive business analytics for all MSEs"""
        from django.db.models import Count, Avg, Sum
        from django.utils import timezone
        from datetime import timedelta
        
        # Time-based filtering
        period = request.query_params.get('period', '30')  # days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=int(period))
        
        # Basic counts
        total_mses = MSE.objects.count()
        active_mses = MSE.objects.filter(status='active').count()
        new_mses = MSE.objects.filter(created_at__date__gte=start_date).count()
        
        # Business type distribution
        business_type_distribution = MSE.objects.values('business_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # MSE type distribution
        mse_type_distribution = MSE.objects.values('mse_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Growth trends
        growth_data = []
        for i in range(7):  # Last 7 periods
            period_start = end_date - timedelta(days=(i+1)*int(period)//7)
            period_end = end_date - timedelta(days=i*int(period)//7)
            period_count = MSE.objects.filter(
                created_at__date__gte=period_start,
                created_at__date__lt=period_end
            ).count()
            growth_data.append({
                'period': period_start.strftime('%Y-%m-%d'),
                'new_mses': period_count
            })
        
        # Performance metrics
        performance_metrics = {
            'total_mses': total_mses,
            'active_mses': active_mses,
            'new_mses': new_mses,
            'activation_rate': (active_mses / total_mses * 100) if total_mses > 0 else 0,
            'growth_rate': (new_mses / total_mses * 100) if total_mses > 0 else 0,
            'business_type_distribution': list(business_type_distribution),
            'mse_type_distribution': list(mse_type_distribution),
            'growth_trends': list(reversed(growth_data))
        }
        
        return Response(performance_metrics)

    @action(detail=True, methods=['get'])
    def performance_metrics(self, request, pk=None):
        """Get detailed performance metrics for a specific MSE"""
        mse = self.get_object()
        
        # Wallet performance
        wallets = Wallet.objects.filter(mse=mse)
        total_balance = sum(wallet.balance for wallet in wallets)
        transaction_count = sum(wallet.transaction_count for wallet in wallets)
        
        # Business metrics based on MSE type
        business_metrics = {}
        
        if hasattr(mse, 'inputmse'):
            input_mse = mse.inputmse
            business_metrics.update({
                'supplier_network_size': input_mse.supplier_network_size,
                'average_order_value': input_mse.average_order_value,
                'input_costs_tracking': input_mse.input_costs_tracking,
                'quality_standards': input_mse.quality_standards
            })
        
        if hasattr(mse, 'productionmse'):
            production_mse = mse.productionmse
            business_metrics.update({
                'daily_production_target': production_mse.daily_production_target,
                'production_process': production_mse.production_process,
                'quality_control': production_mse.quality_control
            })
        
        if hasattr(mse, 'outputmse'):
            output_mse = mse.outputmse
            business_metrics.update({
                'customer_network_size': output_mse.customer_network_size,
                'average_sale_value': output_mse.average_sale_value,
                'market_reach': output_mse.market_reach
            })
        
        return Response({
            'mse_id': mse.id,
            'mse_name': mse.name,
            'mse_type': mse.mse_type,
            'business_type': mse.business_type,
            'status': mse.status,
            'financial_performance': {
                'total_balance': total_balance,
                'transaction_count': transaction_count,
                'wallet_count': wallets.count()
            },
            'business_metrics': business_metrics,
            'registration_date': mse.created_at,
            'last_updated': mse.updated_at
        })

    @action(detail=False, methods=['get'])
    def value_chain_analysis(self, request):
        """Analyze value chain relationships between MSEs"""
        from django.db.models import Q
        
        # Get all MSEs with their relationships
        input_mses = InputMSE.objects.select_related('mse').all()
        production_mses = ProductionMSE.objects.select_related('mse').all()
        output_mses = OutputMSE.objects.select_related('mse').all()
        
        # Value chain mapping
        value_chain = {
            'input_suppliers': len(input_mses),
            'production_units': len(production_mses),
            'output_distributors': len(output_mses),
            'total_value_chain_participants': len(input_mses) + len(production_mses) + len(output_mses)
        }
        
        # Cross-chain relationships
        cross_chain_relationships = []
        
        # Find MSEs that participate in multiple chain stages
        for mse in MSE.objects.all():
            chain_participation = []
            if hasattr(mse, 'inputmse'):
                chain_participation.append('Input')
            if hasattr(mse, 'productionmse'):
                chain_participation.append('Production')
            if hasattr(mse, 'outputmse'):
                chain_participation.append('Output')
            
            if len(chain_participation) > 1:
                cross_chain_relationships.append({
                    'mse_name': mse.name,
                    'mse_type': mse.mse_type,
                    'chain_stages': chain_participation,
                    'participation_count': len(chain_participation)
                })
        
        value_chain['cross_chain_relationships'] = cross_chain_relationships
        value_chain['cross_chain_participants'] = len(cross_chain_relationships)
        
        return Response(value_chain)


class InputMSEViewSet(viewsets.ModelViewSet):
    """ViewSet for InputMSE model"""
    queryset = InputMSE.objects.all()
    serializer_class = InputMSESerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['input_costs_tracking']
    search_fields = ['mse__name', 'quality_standards']
    ordering_fields = ['supplier_network_size', 'average_order_value', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return InputMSEListSerializer
        return InputMSESerializer

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics for Input MSEs"""
        total_input_mses = InputMSE.objects.count()
        total_suppliers = sum(mse.supplier_network_size for mse in InputMSE.objects.all())
        avg_order_value = sum(mse.average_order_value for mse in InputMSE.objects.all()) / total_input_mses if total_input_mses > 0 else 0
        
        return Response({
            'total_input_mses': total_input_mses,
            'total_suppliers': total_suppliers,
            'average_order_value': avg_order_value,
        })


class OutputMSEViewSet(viewsets.ModelViewSet):
    """ViewSet for OutputMSE model"""
    queryset = OutputMSE.objects.all()
    serializer_class = OutputMSESerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['mse__name', 'marketing_strategy', 'pricing_strategy']
    ordering_fields = ['customer_network_size', 'average_sale_value', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return OutputMSEListSerializer
        return OutputMSESerializer

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics for Output MSEs"""
        total_output_mses = OutputMSE.objects.count()
        total_customers = sum(mse.customer_network_size for mse in OutputMSE.objects.all())
        avg_sale_value = sum(mse.average_sale_value for mse in OutputMSE.objects.all()) / total_output_mses if total_output_mses > 0 else 0
        
        return Response({
            'total_output_mses': total_output_mses,
            'total_customers': total_customers,
            'average_sale_value': avg_sale_value,
        })


class ProductionMSEViewSet(viewsets.ModelViewSet):
    """ViewSet for ProductionMSE model"""
    queryset = ProductionMSE.objects.all()
    serializer_class = ProductionMSESerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['mse__name', 'production_process', 'quality_control']
    ordering_fields = ['daily_production_target', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductionMSEListSerializer
        return ProductionMSESerializer

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics for Production MSEs"""
        total_production_mses = ProductionMSE.objects.count()
        total_production_target = sum(mse.daily_production_target for mse in ProductionMSE.objects.all())
        avg_efficiency = sum(mse.get_production_efficiency() for mse in ProductionMSE.objects.all()) / total_production_mses if total_production_mses > 0 else 0
        
        return Response({
            'total_production_mses': total_production_mses,
            'total_daily_production_target': total_production_target,
            'average_efficiency': avg_efficiency,
        })


class MSECategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for MSECategory model"""
    queryset = MSECategory.objects.all()
    serializer_class = MSECategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['primary_category']
    search_fields = ['mse__name', 'category_description']
    ordering_fields = ['category_performance_score', 'category_growth_rate', 'created_at']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def category_summary(self, request):
        """Get summary of MSEs by category"""
        from django.db.models import Count
        
        category_summary = MSECategory.objects.values('primary_category').annotate(
            count=Count('id')
        ).order_by('primary_category')
        
        return Response(category_summary)

    @action(detail=False, methods=['get'])
    def performance_ranking(self, request):
        """Get MSEs ranked by performance score"""
        top_performers = MSECategory.objects.order_by('-category_performance_score')[:10]
        serializer = self.get_serializer(top_performers, many=True)
        return Response(serializer.data)


class WalletViewSet(viewsets.ModelViewSet):
    """ViewSet for Wallet model"""
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['wallet_type', 'currency', 'is_active']
    search_fields = ['name', 'mse__name', 'account_number']
    ordering_fields = ['balance', 'created_at']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def total_balance(self, request):
        """Get total balance across all wallets"""
        mse_id = request.query_params.get('mse_id', None)
        
        if mse_id:
            wallets = Wallet.objects.filter(mse_id=mse_id, is_active=True)
        else:
            wallets = Wallet.objects.filter(is_active=True)
        
        total_balance = sum(wallet.balance for wallet in wallets)
        
        return Response({
            'total_balance': total_balance,
            'wallet_count': wallets.count(),
        })


class UserRoleViewSet(viewsets.ModelViewSet):
    """ViewSet for UserRole model"""
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['user__username', 'user__email', 'mse__name']
    ordering_fields = ['role', 'created_at']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def by_mse(self, request):
        """Get user roles for a specific MSE"""
        mse_id = request.query_params.get('mse_id', None)
        
        if mse_id:
            roles = UserRole.objects.filter(mse_id=mse_id, is_active=True)
        else:
            roles = UserRole.objects.filter(is_active=True)
        
        serializer = self.get_serializer(roles, many=True)
        return Response(serializer.data)
