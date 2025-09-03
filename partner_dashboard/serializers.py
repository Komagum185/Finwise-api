from rest_framework import serializers
from .models import Beneficiary, DigitalServiceUsage, PartnerDashboard
from mse.models import MSE, Wallet
from loans.models import GroupLoan, LoanProduct
from groups.models import Group, GroupMembership


class BeneficiarySerializer(serializers.ModelSerializer):
    """Serializer for beneficiary data"""
    mse_name = serializers.CharField(source='mse.first_name', read_only=True)
    mse_last_name = serializers.CharField(source='mse.last_name', read_only=True)
    business_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Beneficiary
        fields = [
            'id', 'first_name', 'last_name', 'gender', 'age_group',
            'is_refugee', 'has_disability', 'region', 'district', 'subcounty',
            'contact_number', 'mse_name', 'mse_last_name', 'business_name'
        ]
    
    def get_business_name(self, obj):
        return f"{obj.mse.first_name} {obj.mse.last_name}"


class DigitalServiceUsageSerializer(serializers.ModelSerializer):
    """Serializer for digital service usage data"""
    mse_name = serializers.CharField(source='mse.first_name', read_only=True)
    mse_last_name = serializers.CharField(source='mse.last_name', read_only=True)
    business_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DigitalServiceUsage
        fields = [
            'id', 'service_type', 'service_name', 'usage_frequency',
            'beneficiaries_count', 'region', 'district', 'contact_number',
            'mse_name', 'mse_last_name', 'business_name'
        ]
    
    def get_business_name(self, obj):
        return f"{obj.mse.first_name} {obj.mse.last_name}"


class SummarySerializer(serializers.Serializer):
    """Serializer for dashboard summary metrics"""
    total_mse_digitized = serializers.IntegerField()
    total_project_participants = serializers.IntegerField()
    active_loans_count = serializers.IntegerField()
    digital_service_usage_count = serializers.IntegerField()
    total_beneficiaries = serializers.IntegerField()
    total_groups = serializers.IntegerField()


class GraphDataSerializer(serializers.Serializer):
    """Serializer for chart/graph data"""
    mse_by_region = serializers.DictField()
    participants_by_gender = serializers.DictField()
    loans_over_time = serializers.ListField()
    beneficiaries_by_age = serializers.DictField()
    digital_services_by_type = serializers.DictField()


class DigitizationReportSerializer(serializers.Serializer):
    """Serializer for digitization report"""
    business_name = serializers.CharField()
    business_type = serializers.CharField()
    lead_participant = serializers.CharField()
    region = serializers.CharField()
    district = serializers.CharField()
    beneficiaries = serializers.IntegerField()
    lead_contact_number = serializers.CharField()
    total_beneficiaries = serializers.IntegerField()


class LoanReportSerializer(serializers.Serializer):
    """Serializer for loan report"""
    business_name = serializers.CharField()
    group = serializers.CharField()
    loan_amount_received = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_beneficiaries = serializers.IntegerField()
    loan_product = serializers.CharField()
    status = serializers.CharField()
    disbursed_date = serializers.DateTimeField(allow_null=True)


class DigitalServiceReportSerializer(serializers.Serializer):
    """Serializer for digital service report"""
    service_used = serializers.CharField()
    business_name = serializers.CharField()
    region = serializers.CharField()
    district = serializers.CharField()
    contact = serializers.CharField()
    number_of_beneficiaries = serializers.IntegerField()
    service_type = serializers.CharField()


class PartnerDashboardSerializer(serializers.ModelSerializer):
    """Serializer for partner dashboard access tracking"""
    partner_name = serializers.CharField(source='partner.username', read_only=True)
    
    class Meta:
        model = PartnerDashboard
        fields = ['id', 'partner_name', 'last_access', 'access_count', 'created_at']
        read_only_fields = ['last_access', 'access_count', 'created_at']


class FilterSerializer(serializers.Serializer):
    """Serializer for dashboard filters"""
    age = serializers.ChoiceField(
        choices=[('0-35', 'Youth (0-35)'), ('35+', 'Adult (35+)')],
        required=False,
        allow_blank=True
    )
    gender = serializers.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female')],
        required=False,
        allow_blank=True
    )
    refugee = serializers.BooleanField(required=False)
    disability = serializers.BooleanField(required=False)
    region = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    subcounty = serializers.CharField(required=False, allow_blank=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
