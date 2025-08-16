from rest_framework import serializers
from .models import KYCDocument, BankAccount, MobileMoneyAccount, KYCVerification, VerificationRequest
from users.models import CustomUser


class KYCDocumentSerializer(serializers.ModelSerializer):
    """Serializer for KYC documents"""
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = KYCDocument
        fields = [
            'id', 'user', 'document_type', 'document_type_display', 'document_number',
            'issuing_country', 'issue_date', 'expiry_date', 'file', 'filename',
            'file_size', 'file_size_mb', 'file_type', 'status', 'status_display',
            'verified_by', 'verified_at', 'verification_notes', 'is_expired',
            'uploaded_at', 'updated_at'
        ]
        read_only_fields = ['id', 'document_type_display', 'status_display', 'file_size_mb',
                           'is_expired', 'verified_by', 'verified_at', 'uploaded_at', 'updated_at']
    
    def get_file_size_mb(self, obj):
        return obj.get_file_size_mb()


class KYCDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating KYC documents"""
    
    class Meta:
        model = KYCDocument
        fields = [
            'document_type', 'document_number', 'issuing_country', 'issue_date',
            'expiry_date', 'file'
        ]
    
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
        validated_data['user'] = self.context['request'].user
        validated_data['filename'] = file_obj.name
        validated_data['file_size'] = file_obj.size
        validated_data['file_type'] = file_obj.content_type
        
        return super().create(validated_data)


class BankAccountSerializer(serializers.ModelSerializer):
    """Serializer for bank accounts"""
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = BankAccount
        fields = [
            'id', 'user', 'bank_name', 'branch_name', 'account_number', 'account_type',
            'account_type_display', 'account_holder_name', 'currency', 'is_active',
            'status', 'status_display', 'verified_by', 'verified_at', 'verification_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'account_type_display', 'status_display', 'verified_by',
                           'verified_at', 'created_at', 'updated_at']


class BankAccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bank accounts"""
    
    class Meta:
        model = BankAccount
        fields = [
            'bank_name', 'branch_name', 'account_number', 'account_type',
            'account_holder_name', 'currency'
        ]
    
    def create(self, validated_data):
        """Create bank account with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class MobileMoneyAccountSerializer(serializers.ModelSerializer):
    """Serializer for mobile money accounts"""
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = MobileMoneyAccount
        fields = [
            'id', 'user', 'provider', 'provider_display', 'phone_number', 'account_name',
            'is_active', 'status', 'status_display', 'verified_by', 'verified_at',
            'verification_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'provider_display', 'status_display', 'verified_by',
                           'verified_at', 'created_at', 'updated_at']


class MobileMoneyAccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating mobile money accounts"""
    
    class Meta:
        model = MobileMoneyAccount
        fields = ['provider', 'phone_number', 'account_name']
    
    def create(self, validated_data):
        """Create mobile money account with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class KYCVerificationSerializer(serializers.ModelSerializer):
    """Serializer for KYC verification status"""
    verification_level_display = serializers.CharField(source='get_verification_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    verification_progress = serializers.SerializerMethodField()
    is_fully_verified = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = KYCVerification
        fields = [
            'id', 'user', 'verification_level', 'verification_level_display', 'status',
            'status_display', 'documents_uploaded', 'documents_verified',
            'bank_accounts_verified', 'mobile_accounts_verified', 'verification_progress',
            'is_fully_verified', 'verified_by', 'verified_at', 'verification_notes',
            'required_documents', 'required_bank_accounts', 'required_mobile_accounts',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'verification_level_display', 'status_display',
                           'verification_progress', 'is_fully_verified', 'verified_by',
                           'verified_at', 'created_at', 'updated_at']
    
    def get_verification_progress(self, obj):
        return obj.get_verification_progress()


class KYCVerificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating KYC verification"""
    
    class Meta:
        model = KYCVerification
        fields = [
            'verification_level', 'required_documents', 'required_bank_accounts',
            'required_mobile_accounts'
        ]
    
    def create(self, validated_data):
        """Create KYC verification with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class VerificationRequestSerializer(serializers.ModelSerializer):
    """Serializer for verification requests"""
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = VerificationRequest
        fields = [
            'id', 'user', 'request_type', 'request_type_display', 'title', 'description',
            'document', 'bank_account', 'mobile_account', 'kyc_verification', 'status',
            'status_display', 'priority', 'priority_display', 'reviewed_by', 'reviewed_at',
            'review_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'request_type_display', 'status_display', 'priority_display',
                           'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']


class VerificationRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating verification requests"""
    
    class Meta:
        model = VerificationRequest
        fields = [
            'request_type', 'title', 'description', 'document', 'bank_account',
            'mobile_account', 'kyc_verification', 'priority'
        ]
    
    def create(self, validated_data):
        """Create verification request with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class KYCStatusSerializer(serializers.Serializer):
    """Serializer for overall KYC status"""
    user_id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()
    verification_level = serializers.CharField()
    verification_status = serializers.CharField()
    verification_progress = serializers.DecimalField(max_digits=5, decimal_places=2)
    is_fully_verified = serializers.BooleanField()
    documents_count = serializers.IntegerField()
    verified_documents_count = serializers.IntegerField()
    bank_accounts_count = serializers.IntegerField()
    verified_bank_accounts_count = serializers.IntegerField()
    mobile_accounts_count = serializers.IntegerField()
    verified_mobile_accounts_count = serializers.IntegerField()
    last_updated = serializers.DateTimeField()


class KYCStatisticsSerializer(serializers.Serializer):
    """Serializer for KYC statistics"""
    total_users = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    pending_verifications = serializers.IntegerField()
    rejected_verifications = serializers.IntegerField()
    verification_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_verification_time = serializers.DecimalField(max_digits=10, decimal_places=2)
    documents_uploaded = serializers.IntegerField()
    documents_verified = serializers.IntegerField()
    bank_accounts_verified = serializers.IntegerField()
    mobile_accounts_verified = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    monthly_verifications = serializers.ListField()
