from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Beneficiary, DigitalServiceUsage
from mse.models import MSE
from loans.models import GroupLoan
from groups.models import Group
from groups.models import GroupMembership


def apply_filters(queryset, filters):
    """
    Apply filters to a queryset based on the provided filter parameters
    """
    if not filters:
        return queryset
    
    # Age filter
    if filters.get('age'):
        if filters['age'] == '0-35':
            queryset = queryset.filter(age_group='0-35')
        elif filters['age'] == '35+':
            queryset = queryset.filter(age_group='35+')
    
    # Gender filter
    if filters.get('gender'):
        queryset = queryset.filter(gender=filters['gender'])
    
    # Refugee filter
    if filters.get('refugee') is not None:
        queryset = queryset.filter(is_refugee=filters['refugee'])
    
    # Disability filter
    if filters.get('disability') is not None:
        queryset = queryset.filter(has_disability=filters['disability'])
    
    # Region filter
    if filters.get('region'):
        queryset = queryset.filter(region__icontains=filters['region'])
    
    # District filter
    if filters.get('district'):
        queryset = queryset.filter(district__icontains=filters['district'])
    
    # Subcounty filter
    if filters.get('subcounty'):
        queryset = queryset.filter(subcounty__icontains=filters['subcounty'])
    
    # Date range filter
    if filters.get('start_date'):
        queryset = queryset.filter(created_at__gte=filters['start_date'])
    
    if filters.get('end_date'):
        queryset = queryset.filter(created_at__lte=filters['end_date'])
    
    return queryset


def get_summary_metrics(filters=None):
    """
    Get summary metrics for the dashboard
    """
    # Base querysets
    mse_queryset = MSE.objects.filter(status='approved')
    beneficiary_queryset = Beneficiary.objects.all()
    loan_queryset = GroupLoan.objects.filter(status__in=['approved', 'disbursed'])
    digital_service_queryset = DigitalServiceUsage.objects.all()
    group_queryset = Group.objects.all()
    
    # Apply filters if provided
    if filters:
        # Only apply beneficiary-specific filters to beneficiary queryset
        beneficiary_filters = {k: v for k, v in filters.items() if k in ['age', 'gender', 'refugee', 'disability', 'region', 'district', 'subcounty', 'start_date', 'end_date']}
        if beneficiary_filters:
            beneficiary_queryset = apply_filters(beneficiary_queryset, beneficiary_filters)
        
        # Only apply digital service-specific filters to digital service queryset
        digital_service_filters = {k: v for k, v in filters.items() if k in ['region', 'district', 'start_date', 'end_date']}
        if digital_service_filters:
            digital_service_queryset = apply_filters(digital_service_queryset, digital_service_filters)
    
    # Calculate metrics
    total_mse_digitized = mse_queryset.count()
    total_project_participants = beneficiary_queryset.count()
    active_loans_count = loan_queryset.count()
    digital_service_usage_count = digital_service_queryset.count()
    total_beneficiaries = beneficiary_queryset.count()
    total_groups = group_queryset.count()
    
    return {
        'total_mse_digitized': total_mse_digitized,
        'total_project_participants': total_project_participants,
        'active_loans_count': active_loans_count,
        'digital_service_usage_count': digital_service_usage_count,
        'total_beneficiaries': total_beneficiaries,
        'total_groups': total_groups,
    }


def get_graph_data(filters=None):
    """
    Get data for charts and graphs
    """
    # Base querysets
    beneficiary_queryset = Beneficiary.objects.all()
    mse_queryset = MSE.objects.filter(status='approved')
    loan_queryset = GroupLoan.objects.all()
    digital_service_queryset = DigitalServiceUsage.objects.all()
    
    # Apply filters if provided
    if filters:
        # Only apply beneficiary-specific filters to beneficiary queryset
        beneficiary_filters = {k: v for k, v in filters.items() if k in ['age', 'gender', 'refugee', 'disability', 'region', 'district', 'subcounty', 'start_date', 'end_date']}
        if beneficiary_filters:
            beneficiary_queryset = apply_filters(beneficiary_queryset, beneficiary_filters)
        
        # Only apply digital service-specific filters to digital service queryset
        digital_service_filters = {k: v for k, v in filters.items() if k in ['region', 'district', 'start_date', 'end_date']}
        if digital_service_filters:
            digital_service_queryset = apply_filters(digital_service_queryset, digital_service_filters)
    
    # MSE by region (using location field)
    mse_by_region = {}
    for mse in mse_queryset:
        region = mse.location.split(',')[0] if mse.location else 'Unknown'
        mse_by_region[region] = mse_by_region.get(region, 0) + 1
    
    # Participants by gender
    participants_by_gender = dict(
        beneficiary_queryset.values_list('gender')
        .annotate(count=Count('id'))
        .order_by('gender')
    )
    
    # Beneficiaries by age
    beneficiaries_by_age = dict(
        beneficiary_queryset.values_list('age_group')
        .annotate(count=Count('id'))
        .order_by('age_group')
    )
    
    # Digital services by type
    digital_services_by_type = dict(
        digital_service_queryset.values_list('service_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Loans over time (last 12 months)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=365)
    
    loans_over_time = []
    current_date = start_date
    
    while current_date <= end_date:
        month_start = current_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Check if GroupLoan has created_at field, otherwise use a default count
        try:
            month_loans = loan_queryset.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).count()
        except:
            # If created_at field doesn't exist, use a default count
            month_loans = 0
        
        loans_over_time.append({
            'month': current_date.strftime('%Y-%m'),
            'count': month_loans
        })
        
        current_date = (current_date + timedelta(days=32)).replace(day=1)
    
    return {
        'mse_by_region': mse_by_region,
        'participants_by_gender': participants_by_gender,
        'loans_over_time': loans_over_time,
        'beneficiaries_by_age': beneficiaries_by_age,
        'digital_services_by_type': digital_services_by_type,
    }


def get_digitization_report(filters=None):
    """
    Get digitization report data
    """
    queryset = MSE.objects.filter(status='approved')
    
    if filters:
        # Apply filters through beneficiaries
        beneficiary_filters = {k: v for k, v in filters.items() if k != 'start_date' and k != 'end_date'}
        beneficiary_queryset = apply_filters(Beneficiary.objects.all(), beneficiary_filters)
        mse_ids = beneficiary_queryset.values_list('mse_id', flat=True).distinct()
        queryset = queryset.filter(id__in=mse_ids)
    
    report_data = []
    
    for mse in queryset:
        beneficiaries = Beneficiary.objects.filter(mse=mse)
        if filters:
            beneficiaries = apply_filters(beneficiaries, filters)
        
        total_beneficiaries = beneficiaries.count()
        
        report_data.append({
            'business_name': f"{mse.first_name} {mse.last_name}",
            'business_type': mse.category.name,
            'lead_participant': f"{mse.first_name} {mse.last_name}",
            'region': mse.location.split(',')[0] if mse.location else 'Unknown',
            'district': mse.location.split(',')[1] if mse.location and ',' in mse.location else 'Unknown',
            'beneficiaries': total_beneficiaries,
            'lead_contact_number': mse.phone,
            'total_beneficiaries': total_beneficiaries,
        })
    
    return report_data


def get_loan_report(filters=None):
    """
    Get loan report data
    """
    queryset = GroupLoan.objects.all()
    
    if filters:
        # Apply filters through beneficiaries
        beneficiary_filters = {k: v for k, v in filters.items() if k != 'start_date' and k != 'end_date'}
        beneficiary_queryset = apply_filters(Beneficiary.objects.all(), beneficiary_filters)
        mse_ids = beneficiary_queryset.values_list('mse_id', flat=True).distinct()
        
        # Get groups that have these MSEs as members
        group_ids = GroupMembership.objects.filter(mse_id__in=mse_ids).values_list('group_id', flat=True).distinct()
        queryset = queryset.filter(group_id__in=group_ids)
    
    report_data = []
    
    for loan in queryset:
        # Count beneficiaries for this group
        group_members = GroupMembership.objects.filter(group=loan.group)
        total_beneficiaries = Beneficiary.objects.filter(
            mse_id__in=group_members.values_list('mse_id', flat=True)
        ).count()
        
        if filters:
            beneficiary_filters = {k: v for k, v in filters.items() if k != 'start_date' and k != 'end_date'}
            filtered_beneficiaries = apply_filters(
                Beneficiary.objects.filter(mse_id__in=group_members.values_list('mse_id', flat=True)),
                beneficiary_filters
            )
            total_beneficiaries = filtered_beneficiaries.count()
        
        report_data.append({
            'business_name': loan.group.name,
            'group': loan.group.name,
            'loan_amount_received': loan.amount,
            'total_beneficiaries': total_beneficiaries,
            'loan_product': loan.product.name,
            'status': loan.status,
            'disbursed_date': loan.disbursed_at,
        })
    
    return report_data


def get_digital_service_report(filters=None):
    """
    Get digital service report data
    """
    queryset = DigitalServiceUsage.objects.all()
    
    if filters:
        queryset = apply_filters(queryset, filters)
    
    report_data = []
    
    for service in queryset:
        report_data.append({
            'service_used': service.service_name,
            'business_name': f"{service.mse.first_name} {service.mse.last_name}",
            'region': service.region,
            'district': service.district,
            'contact': service.contact_number,
            'number_of_beneficiaries': service.beneficiaries_count,
            'service_type': service.service_type,
        })
    
    return report_data
