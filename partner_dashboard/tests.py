from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
import json

from .models import Beneficiary, DigitalServiceUsage, PartnerDashboard
from mse.models import MSECategory, MSE
from groups.models import Group, GroupMembership
from loans.models import LoanProduct, GroupLoan

User = get_user_model()


class PartnerDashboardTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create MSE categories
        self.input_category = MSECategory.objects.create(
            name='input',
            description='Agricultural inputs'
        )
        self.producer_category = MSECategory.objects.create(
            name='producer',
            description='Agricultural producers'
        )
        
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            password='password123',
            role='admin',
            first_name='Admin',
            last_name='User',
            phone_number='+256700000000',
            NIN='ADMIN123456789',
            is_approved=True
        )
        
        self.partner_viewer = User.objects.create_user(
            username='partner_viewer',
            password='password123',
            role='partner',
            rights='viewer',
            first_name='Partner',
            last_name='Viewer',
            phone_number='+256700000001',
            NIN='PARTNER123456789',
            is_approved=True
        )
        
        self.partner_export = User.objects.create_user(
            username='partner_export',
            password='password123',
            role='partner',
            rights='export',
            first_name='Partner',
            last_name='Export',
            phone_number='+256700000002',
            NIN='PARTNER123456790',
            is_approved=True
        )
        
        self.mse_user = User.objects.create_user(
            username='mse_user',
            password='password123',
            role='mse',
            first_name='MSE',
            last_name='User',
            phone_number='+256700000003',
            NIN='MSE123456789',
            is_approved=True
        )
        
        # Create MSEs
        self.mse1 = MSE.objects.create(
            owner=self.mse_user,
            first_name='John',
            last_name='Farmer',
            nin='MSE123456789',
            phone='+256700000003',
            category=self.producer_category,
            location='Kampala, Uganda',
            status='approved'
        )
        
        self.mse2 = MSE.objects.create(
            owner=self.mse_user,
            first_name='Mary',
            last_name='Supplier',
            nin='MSE123456790',
            phone='+256700000004',
            category=self.input_category,
            location='Jinja, Uganda',
            status='approved'
        )
        
        # Create beneficiaries
        self.beneficiary1 = Beneficiary.objects.create(
            mse=self.mse1,
            first_name='Alice',
            last_name='Johnson',
            gender='female',
            age_group='0-35',
            is_refugee=False,
            has_disability=False,
            region='Kampala',
            district='Central',
            subcounty='Kampala Central',
            contact_number='+256700000005'
        )
        
        self.beneficiary2 = Beneficiary.objects.create(
            mse=self.mse1,
            first_name='Bob',
            last_name='Smith',
            gender='male',
            age_group='35+',
            is_refugee=True,
            has_disability=False,
            region='Kampala',
            district='Central',
            subcounty='Kampala Central',
            contact_number='+256700000006'
        )
        
        # Create digital service usage
        self.digital_service = DigitalServiceUsage.objects.create(
            mse=self.mse1,
            service_type='mobile_money',
            service_name='Mobile Money Transfer',
            usage_frequency='monthly',
            beneficiaries_count=2,
            region='Kampala',
            district='Central',
            contact_number='+256700000003'
        )
        
        # Create groups
        self.group = Group.objects.create(
            name='Test Group',
            description='Test group for loans',
            created_by=self.mse_user
        )
        
        # Create group membership
        self.group_membership = GroupMembership.objects.create(
            group=self.group,
            mse=self.mse1,
            is_active=True
        )
        
        # Create loan product
        self.loan_product = LoanProduct.objects.create(
            name='Test Loan Product',
            interest_rate=Decimal('15.00'),
            max_amount=Decimal('1000000.00'),
            repayment_period_months=12,
            is_active=True
        )
        
        # Create group loan
        self.group_loan = GroupLoan.objects.create(
            group=self.group,
            product=self.loan_product,
            amount=Decimal('500000.00'),
            status='approved'
        )
        
        # Set up API client
        self.client = APIClient()
    
    def test_partner_viewer_access_summaries(self):
        """Test that partner viewer can access summaries"""
        self.client.force_authenticate(user=self.partner_viewer)
        response = self.client.get(reverse('partner_dashboard:dashboard_summaries'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('total_mse_digitized', data)
        self.assertIn('total_project_participants', data)
        self.assertIn('active_loans_count', data)
    
    def test_partner_export_access_summaries(self):
        """Test that partner export can access summaries"""
        self.client.force_authenticate(user=self.partner_export)
        response = self.client.get(reverse('partner_dashboard:dashboard_summaries'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_non_partner_denied_access(self):
        """Test that non-partner users are denied access"""
        self.client.force_authenticate(user=self.mse_user)
        response = self.client.get(reverse('partner_dashboard:dashboard_summaries'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_denied_access(self):
        """Test that unauthenticated users are denied access"""
        response = self.client.get(reverse('partner_dashboard:dashboard_summaries'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_summaries_with_filters(self):
        """Test summaries endpoint with filters"""
        self.client.force_authenticate(user=self.partner_viewer)
        
        # Test age filter
        response = self.client.get(
            reverse('partner_dashboard:dashboard_summaries'),
            {'age': '0-35'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test gender filter
        response = self.client.get(
            reverse('partner_dashboard:dashboard_summaries'),
            {'gender': 'female'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test region filter
        response = self.client.get(
            reverse('partner_dashboard:dashboard_summaries'),
            {'region': 'Kampala'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_graphs_endpoint(self):
        """Test graphs endpoint"""
        self.client.force_authenticate(user=self.partner_viewer)
        response = self.client.get(reverse('partner_dashboard:dashboard_graphs'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('mse_by_region', data)
        self.assertIn('participants_by_gender', data)
        self.assertIn('loans_over_time', data)
    
    def test_digitization_report(self):
        """Test digitization report endpoint"""
        self.client.force_authenticate(user=self.partner_viewer)
        response = self.client.get(reverse('partner_dashboard:digitization_report'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('count', data)
        self.assertGreater(data['count'], 0)
    
    def test_loan_report(self):
        """Test loan report endpoint"""
        self.client.force_authenticate(user=self.partner_viewer)
        response = self.client.get(reverse('partner_dashboard:loan_report'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('count', data)
        self.assertGreater(data['count'], 0)
    
    def test_digital_service_report(self):
        """Test digital service report endpoint"""
        self.client.force_authenticate(user=self.partner_viewer)
        response = self.client.get(reverse('partner_dashboard:digital_service_report'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('count', data)
        self.assertGreater(data['count'], 0)
    
    def test_export_permission_viewer_denied(self):
        """Test that partner viewer cannot export"""
        self.client.force_authenticate(user=self.partner_viewer)
        response = self.client.get(
            reverse('partner_dashboard:export_report', kwargs={'report_type': 'digitization'}),
            {'format': 'csv'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_export_permission_export_allowed(self):
        """Test that partner export can export"""
        self.client.force_authenticate(user=self.partner_export)
        response = self.client.get(
            reverse('partner_dashboard:export_report', kwargs={'report_type': 'digitization'}),
            {'format': 'csv'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
    
    def test_export_csv_format(self):
        """Test CSV export format"""
        self.client.force_authenticate(user=self.partner_export)
        response = self.client.get(
            reverse('partner_dashboard:export_report', kwargs={'report_type': 'digitization'}),
            {'format': 'csv'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('Content-Disposition', response)
    
    def test_export_pdf_format(self):
        """Test PDF export format"""
        self.client.force_authenticate(user=self.partner_export)
        response = self.client.get(
            reverse('partner_dashboard:export_report', kwargs={'report_type': 'digitization'}),
            {'format': 'pdf'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('Content-Disposition', response)
    
    def test_invalid_export_format(self):
        """Test invalid export format"""
        self.client.force_authenticate(user=self.partner_export)
        response = self.client.get(
            reverse('partner_dashboard:export_report', kwargs={'report_type': 'digitization'}),
            {'format': 'invalid'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_report_type(self):
        """Test invalid report type"""
        self.client.force_authenticate(user=self.partner_export)
        response = self.client.get(
            reverse('partner_dashboard:export_report', kwargs={'report_type': 'invalid'}),
            {'format': 'csv'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_report_list_endpoint(self):
        """Test report list endpoint"""
        self.client.force_authenticate(user=self.partner_viewer)
        response = self.client.get(reverse('partner_dashboard:report_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('reports', data)
        self.assertIn('export_formats', data)
        self.assertIn('filters', data)
    
    def test_dashboard_access_log(self):
        """Test dashboard access log endpoint"""
        self.client.force_authenticate(user=self.partner_viewer)
        response = self.client.get(reverse('partner_dashboard:dashboard_access_log'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('last_access', data)
        self.assertIn('access_count', data)
    
    def test_pagination(self):
        """Test pagination in reports"""
        self.client.force_authenticate(user=self.partner_viewer)
        response = self.client.get(
            reverse('partner_dashboard:digitization_report'),
            {'page': 1, 'page_size': 10}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)
        self.assertIn('num_pages', data)
        self.assertIn('current_page', data)
    
    def test_partner_dashboard_creation_signal(self):
        """Test that partner dashboard is created when partner user is created"""
        # Create a new partner user
        new_partner = User.objects.create_user(
            username='new_partner',
            password='password123',
            role='partner',
            rights='viewer',
            first_name='New',
            last_name='Partner',
            phone_number='+256700000007',
            NIN='NEWPARTNER123',
            is_approved=True
        )
        
        # Check if partner dashboard was created
        dashboard = PartnerDashboard.objects.filter(partner=new_partner).first()
        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard.access_count, 0)
    
    def test_beneficiary_model(self):
        """Test beneficiary model"""
        beneficiary = Beneficiary.objects.create(
            mse=self.mse2,
            first_name='Test',
            last_name='Beneficiary',
            gender='male',
            age_group='0-35',
            is_refugee=False,
            has_disability=True,
            region='Jinja',
            district='Jinja',
            subcounty='Jinja Central',
            contact_number='+256700000008'
        )
        
        self.assertEqual(beneficiary.mse, self.mse2)
        self.assertEqual(beneficiary.gender, 'male')
        self.assertEqual(beneficiary.age_group, '0-35')
        self.assertFalse(beneficiary.is_refugee)
        self.assertTrue(beneficiary.has_disability)
    
    def test_digital_service_usage_model(self):
        """Test digital service usage model"""
        service = DigitalServiceUsage.objects.create(
            mse=self.mse2,
            service_type='digital_banking',
            service_name='Online Banking',
            usage_frequency='weekly',
            beneficiaries_count=3,
            region='Jinja',
            district='Jinja',
            contact_number='+256700000009'
        )
        
        self.assertEqual(service.mse, self.mse2)
        self.assertEqual(service.service_type, 'digital_banking')
        self.assertEqual(service.usage_frequency, 'weekly')
        self.assertEqual(service.beneficiaries_count, 3)
