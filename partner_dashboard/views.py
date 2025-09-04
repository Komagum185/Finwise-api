from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from .permissions import FullAccess, CanExport
from .serializers import (
    SummarySerializer, GraphDataSerializer, DigitizationReportSerializer,
    LoanReportSerializer, DigitalServiceReportSerializer, FilterSerializer
)
from .utils import (
    get_summary_metrics, get_graph_data, get_digitization_report,
    get_loan_report, get_digital_service_report, apply_filters
)
from .export_utils import (
    export_to_csv, export_to_pdf, get_export_filename,
    get_field_labels, get_fieldnames
)
from .models import PartnerDashboard


@api_view(['GET'])
@permission_classes([FullAccess])
def dashboard_summaries(request):
    """
    Get dashboard summary metrics
    """
    try:
        # Parse filters from query parameters
        filters = {}
        for key, value in request.query_params.items():
            if value and value.lower() not in ['null', 'undefined', '']:
                filters[key] = value
        
        # Get summary metrics
        summary_data = get_summary_metrics(filters)
        
        # Track dashboard access
        dashboard, created = PartnerDashboard.objects.get_or_create(
            partner=request.user,
            defaults={'access_count': 1}
        )
        if not created:
            dashboard.access_count += 1
            dashboard.save()
        
        serializer = SummarySerializer(summary_data)
        return Response(serializer.data)
    
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch summary data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([FullAccess])
def dashboard_graphs(request):
    """
    Get data for charts and graphs
    """
    try:
        # Parse filters from query parameters
        filters = {}
        for key, value in request.query_params.items():
            if value and value.lower() not in ['null', 'undefined', '']:
                filters[key] = value
        
        # Get graph data
        graph_data = get_graph_data(filters)
        
        serializer = GraphDataSerializer(graph_data)
        return Response(serializer.data)
    
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch graph data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([FullAccess])
def digitization_report(request):
    """
    Get digitization report data
    """
    try:
        # Parse filters from query parameters
        filters = {}
        for key, value in request.query_params.items():
            if value and value.lower() not in ['null', 'undefined', '']:
                filters[key] = value
        
        # Get report data
        report_data = get_digitization_report(filters)
        
        # Pagination
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 50)
        
        paginator = Paginator(report_data, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = DigitizationReportSerializer(page_obj.object_list, many=True)
        
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'num_pages': paginator.num_pages,
            'current_page': page_obj.number,
        })
    
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch digitization report: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([FullAccess])
def loan_report(request):
    """
    Get loan report data
    """
    try:
        # Parse filters from query parameters
        filters = {}
        for key, value in request.query_params.items():
            if value and value.lower() not in ['null', 'undefined', '']:
                filters[key] = value
        
        # Get report data
        report_data = get_loan_report(filters)
        
        # Pagination
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 50)
        
        paginator = Paginator(report_data, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = LoanReportSerializer(page_obj.object_list, many=True)
        
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'num_pages': paginator.num_pages,
            'current_page': page_obj.number,
        })
    
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch loan report: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([FullAccess])
def digital_service_report(request):
    """
    Get digital service report data
    """
    try:
        # Parse filters from query parameters
        filters = {}
        for key, value in request.query_params.items():
            if value and value.lower() not in ['null', 'undefined', '']:
                filters[key] = value
        
        # Get report data
        report_data = get_digital_service_report(filters)
        
        # Pagination
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 50)
        
        paginator = Paginator(report_data, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = DigitalServiceReportSerializer(page_obj.object_list, many=True)
        
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'num_pages': paginator.num_pages,
            'current_page': page_obj.number,
        })
    
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch digital service report: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([FullAccess, CanExport])
def export_report(request, report_type=None):
    """
    Export report data in CSV or PDF format
    """
    try:
        # Check if user has export rights
        if request.user.rights != 'export':
            return Response(
                {'error': 'You do not have permission to export data. Contact administrator for export rights.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get report_type from kwargs if not provided as parameter
        if report_type is None:
            report_type = request.resolver_match.kwargs.get('report_type')
        
        # Validate report type
        valid_report_types = ['digitization', 'loans', 'digital_services']
        if report_type not in valid_report_types:
            return Response(
                {'error': f'Invalid report type. Must be one of: {", ".join(valid_report_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse filters from query parameters
        filters = {}
        for key, value in request.query_params.items():
            if key != 'format' and value and value.lower() not in ['null', 'undefined', '']:
                filters[key] = value
        
        # Get report data based on type
        if report_type == 'digitization':
            report_data = get_digitization_report(filters)
            title = "Digitization Report"
        elif report_type == 'loans':
            report_data = get_loan_report(filters)
            title = "Loan Report"
        elif report_type == 'digital_services':
            report_data = get_digital_service_report(filters)
            title = "Digital Service Report"
        
        # Get export format from kwargs or query params
        export_format = request.resolver_match.kwargs.get('format') or request.query_params.get('format', 'csv')
        export_format = export_format.lower()
        
        # Get field names and labels
        fieldnames = get_fieldnames(report_type)
        field_labels = get_field_labels(report_type)
        
        # Generate filename
        filename = get_export_filename(report_type, export_format)
        
        # Export based on format
        if export_format == 'csv':
            return export_to_csv(report_data, filename, fieldnames)
        elif export_format == 'pdf':
            return export_to_pdf(report_data, filename, title, fieldnames, field_labels)
        else:
            return Response(
                {'error': f'Invalid export format: {export_format}. Must be "csv" or "pdf"'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        return Response(
            {'error': f'Failed to export report: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([FullAccess])
def report_list(request):
    """
    Get list of available reports
    """
    reports = [
        {
            'type': 'digitization',
            'name': 'Digitization Report',
            'description': 'Report showing MSE digitization status and beneficiary information',
            'endpoint': '/api/partner-dashboard/reports/digitization/',
            'export_endpoint': '/api/partner-dashboard/reports/digitization/export/'
        },
        {
            'type': 'loans',
            'name': 'Loan Report',
            'description': 'Report showing loan information and group beneficiary details',
            'endpoint': '/api/partner-dashboard/reports/loans/',
            'export_endpoint': '/api/partner-dashboard/reports/loans/export/'
        },
        {
            'type': 'digital_services',
            'name': 'Digital Service Report',
            'description': 'Report showing digital service usage by MSEs',
            'endpoint': '/api/partner-dashboard/reports/digital-services/',
            'export_endpoint': '/api/partner-dashboard/reports/digital-services/export/'
        }
    ]
    
    return Response({
        'reports': reports,
        'export_formats': ['csv', 'pdf'],
        'filters': {
            'age': ['0-35', '35+'],
            'gender': ['male', 'female'],
            'refugee': [True, False],
            'disability': [True, False],
            'region': 'string',
            'district': 'string',
            'subcounty': 'string',
            'start_date': 'YYYY-MM-DD',
            'end_date': 'YYYY-MM-DD'
        }
    })


@api_view(['GET'])
@permission_classes([FullAccess])
def dashboard_access_log(request):
    """
    Get dashboard access log for the current partner
    """
    try:
        dashboard = get_object_or_404(PartnerDashboard, partner=request.user)
        return Response({
            'last_access': dashboard.last_access,
            'access_count': dashboard.access_count,
            'created_at': dashboard.created_at
        })
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch access log: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([FullAccess])
def filter_options(request):
    """
    Get available filter options for the partner dashboard
    """
    try:
        filter_options = {
            'age_groups': [
                {'value': '0-35', 'label': '18-35 years'},
                {'value': '35+', 'label': '35+ years'}
            ],
            'gender': [
                {'value': 'male', 'label': 'Male'},
                {'value': 'female', 'label': 'Female'}
            ],
            'refugee_status': [
                {'value': True, 'label': 'Refugee'},
                {'value': False, 'label': 'Non-refugee'}
            ],
            'disability_status': [
                {'value': True, 'label': 'With Disability'},
                {'value': False, 'label': 'Without Disability'}
            ],
            'regions': [
                {'value': 'central', 'label': 'Central'},
                {'value': 'eastern', 'label': 'Eastern'},
                {'value': 'northern', 'label': 'Northern'},
                {'value': 'western', 'label': 'Western'}
            ],
            'districts': [
                {'value': 'kampala', 'label': 'Kampala'},
                {'value': 'wakiso', 'label': 'Wakiso'},
                {'value': 'mukono', 'label': 'Mukono'},
                {'value': 'jinja', 'label': 'Jinja'},
                {'value': 'mbale', 'label': 'Mbale'},
                {'value': 'gulu', 'label': 'Gulu'},
                {'value': 'mbarara', 'label': 'Mbarara'},
                {'value': 'fort_portal', 'label': 'Fort Portal'}
            ],
            'subcounties': [
                {'value': 'central_division', 'label': 'Central Division'},
                {'value': 'nakawa_division', 'label': 'Nakawa Division'},
                {'value': 'makindye_division', 'label': 'Makindye Division'},
                {'value': 'rubaga_division', 'label': 'Rubaga Division'},
                {'value': 'kawempe_division', 'label': 'Kawempe Division'}
            ],
            'date_ranges': [
                {'value': 'last_7_days', 'label': 'Last 7 Days'},
                {'value': 'last_30_days', 'label': 'Last 30 Days'},
                {'value': 'last_90_days', 'label': 'Last 90 Days'},
                {'value': 'last_6_months', 'label': 'Last 6 Months'},
                {'value': 'last_year', 'label': 'Last Year'},
                {'value': 'custom', 'label': 'Custom Range'}
            ]
        }
        
        return Response(filter_options)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch filter options: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
