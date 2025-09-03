from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
import random

from partner_dashboard.models import Beneficiary, DigitalServiceUsage
from mse.models import MSE, MSECategory

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate partner dashboard with sample data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing partner dashboard data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing partner dashboard data...')
            self.clear_data()

        self.stdout.write('Populating partner dashboard with sample data...')
        
        try:
            with transaction.atomic():
                self.create_sample_data()
                self.stdout.write(
                    self.style.SUCCESS('Successfully populated partner dashboard with sample data!')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error populating data: {str(e)}')
            )

    def clear_data(self):
        """Clear existing partner dashboard data"""
        DigitalServiceUsage.objects.all().delete()
        Beneficiary.objects.all().delete()

    def create_sample_data(self):
        """Create sample data for partner dashboard"""
        
        # Get existing MSEs
        mses = MSE.objects.filter(status='approved')
        if not mses.exists():
            self.stdout.write(self.style.WARNING('No approved MSEs found. Please run populate_markets_data first.'))
            return
        
        # Create beneficiaries for each MSE
        self.create_beneficiaries(mses)
        
        # Create digital service usage
        self.create_digital_services(mses)

    def create_beneficiaries(self, mses):
        """Create sample beneficiaries"""
        
        # Sample beneficiary data
        beneficiary_data = [
            # Youth beneficiaries
            {'first_name': 'Alice', 'last_name': 'Johnson', 'gender': 'female', 'age_group': '0-35', 'is_refugee': False, 'has_disability': False},
            {'first_name': 'Bob', 'last_name': 'Smith', 'gender': 'male', 'age_group': '0-35', 'is_refugee': False, 'has_disability': False},
            {'first_name': 'Carol', 'last_name': 'Davis', 'gender': 'female', 'age_group': '0-35', 'is_refugee': True, 'has_disability': False},
            {'first_name': 'David', 'last_name': 'Wilson', 'gender': 'male', 'age_group': '0-35', 'is_refugee': False, 'has_disability': True},
            
            # Adult beneficiaries
            {'first_name': 'Emma', 'last_name': 'Brown', 'gender': 'female', 'age_group': '35+', 'is_refugee': False, 'has_disability': False},
            {'first_name': 'Frank', 'last_name': 'Miller', 'gender': 'male', 'age_group': '35+', 'is_refugee': True, 'has_disability': False},
            {'first_name': 'Grace', 'last_name': 'Taylor', 'gender': 'female', 'age_group': '35+', 'is_refugee': False, 'has_disability': True},
            {'first_name': 'Henry', 'last_name': 'Anderson', 'gender': 'male', 'age_group': '35+', 'is_refugee': False, 'has_disability': False},
        ]
        
        # Regions and districts
        regions_districts = [
            ('West Nile', 'Arua', 'Arua Central'),
            ('West Nile', 'Moyo', 'Moyo Central'),
            ('Karamoja', 'Kotido', 'Kotido Central'),
            ('Karamoja', 'Moroto', 'Moroto Central'),
            ('South Western', 'Mbarara', 'Mbarara Central'),
            ('South Western', 'Kabale', 'Kabale Central'),
            ('Northern', 'Gulu', 'Gulu Central'),
            ('Northern', 'Lira', 'Lira Central'),
        ]
        
        beneficiaries_created = 0
        
        for mse in mses:
            # Create 2-4 beneficiaries for each MSE
            num_beneficiaries = random.randint(2, 4)
            selected_beneficiaries = random.sample(beneficiary_data, min(num_beneficiaries, len(beneficiary_data)))
            
            for beneficiary_info in selected_beneficiaries:
                # Randomly select region and district
                region, district, subcounty = random.choice(regions_districts)
                
                beneficiary = Beneficiary.objects.create(
                    mse=mse,
                    first_name=beneficiary_info['first_name'],
                    last_name=beneficiary_info['last_name'],
                    gender=beneficiary_info['gender'],
                    age_group=beneficiary_info['age_group'],
                    is_refugee=beneficiary_info['is_refugee'],
                    has_disability=beneficiary_info['has_disability'],
                    region=region,
                    district=district,
                    subcounty=subcounty,
                    contact_number=f"+2567{random.randint(10000000, 99999999)}"
                )
                
                beneficiaries_created += 1
        
        self.stdout.write(f'Created {beneficiaries_created} beneficiaries')

    def create_digital_services(self, mses):
        """Create sample digital service usage"""
        
        # Sample digital services
        digital_services = [
            {'service_type': 'mobile_money', 'service_name': 'Mobile Money Transfer', 'usage_frequency': 'daily'},
            {'service_type': 'mobile_money', 'service_name': 'Mobile Money Payments', 'usage_frequency': 'weekly'},
            {'service_type': 'digital_banking', 'service_name': 'Online Banking', 'usage_frequency': 'monthly'},
            {'service_type': 'digital_banking', 'service_name': 'Mobile Banking App', 'usage_frequency': 'weekly'},
            {'service_type': 'e_commerce', 'service_name': 'Online Marketplace', 'usage_frequency': 'monthly'},
            {'service_type': 'digital_marketing', 'service_name': 'Social Media Marketing', 'usage_frequency': 'weekly'},
            {'service_type': 'financial_tools', 'service_name': 'Financial Planning App', 'usage_frequency': 'monthly'},
            {'service_type': 'financial_tools', 'service_name': 'Budget Tracking Tool', 'usage_frequency': 'weekly'},
        ]
        
        # Regions and districts (same as beneficiaries)
        regions_districts = [
            ('West Nile', 'Arua'),
            ('West Nile', 'Moyo'),
            ('Karamoja', 'Kotido'),
            ('Karamoja', 'Moroto'),
            ('South Western', 'Mbarara'),
            ('South Western', 'Kabale'),
            ('Northern', 'Gulu'),
            ('Northern', 'Lira'),
        ]
        
        services_created = 0
        
        for mse in mses:
            # Create 1-3 digital services for each MSE
            num_services = random.randint(1, 3)
            selected_services = random.sample(digital_services, min(num_services, len(digital_services)))
            
            for service_info in selected_services:
                # Randomly select region and district
                region, district = random.choice(regions_districts)
                
                # Get beneficiary count for this MSE
                beneficiary_count = Beneficiary.objects.filter(mse=mse).count()
                
                service = DigitalServiceUsage.objects.create(
                    mse=mse,
                    service_type=service_info['service_type'],
                    service_name=service_info['service_name'],
                    usage_frequency=service_info['usage_frequency'],
                    beneficiaries_count=beneficiary_count,
                    region=region,
                    district=district,
                    contact_number=mse.phone
                )
                
                services_created += 1
        
        self.stdout.write(f'Created {services_created} digital service usage records')
