from rest_framework import serializers
from .models import LoanApplication, Loan, LoanSchedule, LoanPayment, LoanDocument
from mses.models import MSE
from users.models import CustomUser


class LoanApplicationSerializer(serializers.ModelSerializer):
    """Serializer for loan applications"""
    applicant_name = serializers.CharField(source='applicant.get_full_name', read_only=True)
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    
    class Meta:
        model = LoanApplication
        fields = [
            'id', 'applicant', 'applicant_name', 'mse', 'mse_name',
            'requested_amount', 'purpose', 'business_plan', 'collateral_description',
            'status', 'status_display', 'submitted_at', 'reviewed_by', 'reviewed_at',
            'review_notes', 'credit_score', 'risk_level', 'risk_level_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'applicant_name', 'mse_name', 'status_display', 
                           'risk_level_display', 'submitted_at', 'reviewed_at', 
                           'created_at', 'updated_at']


class LoanApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating loan applications"""
    
    class Meta:
        model = LoanApplication
        fields = [
            'mse', 'requested_amount', 'purpose', 'business_plan', 'collateral_description'
        ]
    
    def validate_mse(self, value):
        """Validate that the MSE belongs to the current user"""
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("You can only apply for loans for your own MSEs")
        return value
    
    def create(self, validated_data):
        """Create loan application with current user as applicant"""
        validated_data['applicant'] = self.context['request'].user
        return super().create(validated_data)


class LoanApplicationReviewSerializer(serializers.ModelSerializer):
    """Serializer for reviewing loan applications"""
    
    class Meta:
        model = LoanApplication
        fields = ['status', 'review_notes', 'credit_score', 'risk_level']
    
    def validate_status(self, value):
        """Validate status transition"""
        instance = self.instance
        if instance and instance.status == 'approved' and value != 'approved':
            raise serializers.ValidationError("Cannot change status of approved application")
        return value


class LoanScheduleSerializer(serializers.ModelSerializer):
    """Serializer for loan payment schedules"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = LoanSchedule
        fields = [
            'id', 'loan', 'payment_number', 'due_date', 'principal_due', 'interest_due',
            'total_due', 'balance_after_payment', 'amount_paid', 'payment_date',
            'status', 'status_display', 'days_overdue', 'late_fees', 'remaining_amount',
            'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status_display', 'remaining_amount', 'is_overdue',
                           'days_overdue', 'late_fees', 'created_at', 'updated_at']


class LoanPaymentSerializer(serializers.ModelSerializer):
    """Serializer for loan payments"""
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = LoanPayment
        fields = [
            'id', 'loan', 'schedule', 'amount', 'payment_method', 'payment_method_display',
            'reference', 'notes', 'wallet_transaction', 'payment_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'payment_method_display', 'payment_date', 'created_at', 'updated_at']


class LoanPaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating loan payments"""
    
    class Meta:
        model = LoanPayment
        fields = ['loan', 'schedule', 'amount', 'payment_method', 'reference', 'notes']
    
    def validate(self, data):
        """Validate payment data"""
        loan = data['loan']
        schedule = data['schedule']
        amount = data['amount']
        
        # Validate schedule belongs to loan
        if schedule.loan != loan:
            raise serializers.ValidationError("Schedule does not belong to the specified loan")
        
        # Validate amount doesn't exceed remaining amount
        remaining = schedule.get_remaining_amount()
        if amount > remaining:
            raise serializers.ValidationError(f"Payment amount cannot exceed remaining amount of {remaining}")
        
        return data


class LoanDocumentSerializer(serializers.ModelSerializer):
    """Serializer for loan documents"""
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = LoanDocument
        fields = [
            'id', 'loan_application', 'loan', 'document_type', 'document_type_display',
            'file', 'filename', 'file_size', 'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
        read_only_fields = ['id', 'document_type_display', 'uploaded_by_name', 
                           'filename', 'file_size', 'uploaded_at']


class LoanDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating loan documents"""
    
    class Meta:
        model = LoanDocument
        fields = ['loan_application', 'loan', 'document_type', 'file']
    
    def validate_file(self, value):
        """Validate uploaded file"""
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB")
        
        # Check file type
        allowed_types = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in allowed_types:
            raise serializers.ValidationError(f"File type not allowed. Allowed types: {', '.join(allowed_types)}")
        
        return value
    
    def create(self, validated_data):
        """Create document with current user and file info"""
        file_obj = validated_data['file']
        validated_data['uploaded_by'] = self.context['request'].user
        validated_data['filename'] = file_obj.name
        validated_data['file_size'] = file_obj.size
        return super().create(validated_data)


class LoanSerializer(serializers.ModelSerializer):
    """Serializer for loans"""
    loan_type_display = serializers.CharField(source='get_loan_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_frequency_display = serializers.CharField(source='get_payment_frequency_display', read_only=True)
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    monthly_payment = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_amount_due = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    remaining_balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Loan
        fields = [
            'id', 'application', 'mse', 'mse_name', 'loan_type', 'loan_type_display',
            'principal_amount', 'interest_rate', 'term_months', 'payment_frequency',
            'payment_frequency_display', 'status', 'status_display', 'disbursed_at',
            'maturity_date', 'total_interest', 'total_paid', 'outstanding_balance',
            'days_past_due', 'late_fees_charged', 'monthly_payment', 'total_amount_due',
            'remaining_balance', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'loan_type_display', 'status_display', 'payment_frequency_display',
                           'mse_name', 'monthly_payment', 'total_amount_due', 'remaining_balance',
                           'disbursed_at', 'created_at', 'updated_at']


class LoanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating loans from approved applications"""
    
    class Meta:
        model = Loan
        fields = [
            'application', 'loan_type', 'principal_amount', 'interest_rate', 
            'term_months', 'payment_frequency'
        ]
    
    def validate_application(self, value):
        """Validate application is approved"""
        if value.status != 'approved':
            raise serializers.ValidationError("Can only create loans from approved applications")
        return value
    
    def validate_principal_amount(self, value):
        """Validate principal amount matches requested amount"""
        application = self.initial_data.get('application')
        if application:
            try:
                app = LoanApplication.objects.get(id=application)
                if value > app.requested_amount:
                    raise serializers.ValidationError("Principal amount cannot exceed requested amount")
            except LoanApplication.DoesNotExist:
                pass
        return value


class LoanSummarySerializer(serializers.ModelSerializer):
    """Serializer for loan summary information"""
    loan_type_display = serializers.CharField(source='get_loan_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    next_payment = serializers.SerializerMethodField()
    overdue_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Loan
        fields = [
            'id', 'mse_name', 'loan_type_display', 'principal_amount', 'interest_rate',
            'term_months', 'status_display', 'outstanding_balance', 'next_payment',
            'overdue_amount', 'days_past_due', 'maturity_date'
        ]
    
    def get_next_payment(self, obj):
        """Get next payment information"""
        next_schedule = obj.schedule.filter(status='pending').first()
        if next_schedule:
            return {
                'due_date': next_schedule.due_date,
                'amount': next_schedule.total_due,
                'remaining': next_schedule.get_remaining_amount()
            }
        return None
    
    def get_overdue_amount(self, obj):
        """Get total overdue amount"""
        overdue_schedules = obj.schedule.filter(status='overdue')
        return sum(schedule.get_remaining_amount() for schedule in overdue_schedules)


class LoanAnalyticsSerializer(serializers.Serializer):
    """Serializer for loan analytics"""
    total_loans = serializers.IntegerField()
    active_loans = serializers.IntegerField()
    total_disbursed = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_outstanding = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_repaid = serializers.DecimalField(max_digits=15, decimal_places=2)
    overdue_loans = serializers.IntegerField()
    overdue_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_loan_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    repayment_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    monthly_disbursements = serializers.ListField()
    monthly_repayments = serializers.ListField()
