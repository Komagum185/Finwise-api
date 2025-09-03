from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
import random
from datetime import datetime, timedelta

from mse.models import MSECategory, MSE, Wallet
from markets.models import Customer, Supplier, Product, Transaction, Notification
from groups.models import Group, GroupMembership, GroupWallet
from loans.models import LoanProduct, GroupLoan, GroupLoanRepayment

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with sample market data for testing and development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        self.stdout.write('Populating database with sample market data...')
        
        try:
            with transaction.atomic():
                self.create_sample_data()
                self.stdout.write(
                    self.style.SUCCESS('Successfully populated database with sample data!')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error populating data: {str(e)}')
            )

    def clear_data(self):
        """Clear existing data"""
        # Clear loans data first
        GroupLoanRepayment.objects.all().delete()
        GroupLoan.objects.all().delete()
        LoanProduct.objects.all().delete()
        
        # Clear groups data
        GroupWallet.objects.all().delete()
        GroupMembership.objects.all().delete()
        Group.objects.all().delete()
        
        # Clear markets data
        Notification.objects.all().delete()
        Transaction.objects.all().delete()
        Product.objects.all().delete()
        Customer.objects.all().delete()
        Supplier.objects.all().delete()
        Wallet.objects.all().delete()
        MSE.objects.all().delete()
        MSECategory.objects.all().delete()
        
        # Clear users except superuser
        User.objects.filter(is_superuser=False).delete()

    def create_sample_data(self):
        """Create sample data for all models"""
        
        # Create MSE Categories
        categories = self.create_mse_categories()
        
        # Create Users and MSEs
        users_and_mses = self.create_users_and_mses(categories)
        
        # Create Wallets
        wallets = self.create_wallets(users_and_mses)
        
        # Create Groups and Group Memberships
        groups_and_memberships = self.create_groups_and_memberships(users_and_mses)
        
        # Create Group Wallets
        group_wallets = self.create_group_wallets(groups_and_memberships)
        
        # Create Loan Products
        loan_products = self.create_loan_products()
        
        # Create Group Loans
        group_loans = self.create_group_loans(groups_and_memberships, loan_products, users_and_mses)
        
        # Create Group Loan Repayments
        loan_repayments = self.create_loan_repayments(group_loans)
        
        # Create Products
        products = self.create_products(users_and_mses)
        
        # Create Customers and Suppliers
        customers = self.create_customers(users_and_mses)
        suppliers = self.create_suppliers(users_and_mses)
        
        # Create Transactions
        transactions = self.create_transactions(users_and_mses, products, customers, suppliers)
        
        # Create Notifications
        notifications = self.create_notifications(users_and_mses)

    def create_mse_categories(self):
        """Create MSE categories"""
        categories = []
        category_data = [
            {'name': 'input', 'description': 'Agricultural inputs and supplies'},
            {'name': 'producer', 'description': 'Agricultural producers and farmers'},
            {'name': 'output', 'description': 'Agricultural output and processing'},
        ]
        
        for data in category_data:
            category, created = MSECategory.objects.get_or_create(
                name=data['name'],
                defaults={'description': data['description']}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created MSE category: {category.name}')
        
        return categories

    def create_users_and_mses(self, categories):
        """Create sample users and MSEs"""
        users_and_mses = []
        
        # Sample data for users and MSEs
        sample_data = [
            {
                'username': 'john_farmer',
                'first_name': 'John',
                'last_name': 'Farmer',
                'phone_number': '+256701234567',
                'NIN': 'CM123456789ABCDEF',
                'role': 'mse',
                'email': 'john.farmer@example.com',
                'category': categories[1],  # producer
                'location': 'Kampala, Uganda',
                'status': 'approved'
            },
            {
                'username': 'mary_supplier',
                'first_name': 'Mary',
                'last_name': 'Supplier',
                'phone_number': '+256702345678',
                'NIN': 'CM234567890BCDEFG',
                'role': 'mse',
                'email': 'mary.supplier@example.com',
                'category': categories[0],  # input
                'location': 'Jinja, Uganda',
                'status': 'approved'
            },
            {
                'username': 'peter_processor',
                'first_name': 'Peter',
                'last_name': 'Processor',
                'phone_number': '+256703456789',
                'NIN': 'CM345678901CDEFGH',
                'role': 'mse',
                'email': 'peter.processor@example.com',
                'category': categories[2],  # output
                'location': 'Mukono, Uganda',
                'status': 'approved'
            },
            {
                'username': 'sarah_trader',
                'first_name': 'Sarah',
                'last_name': 'Trader',
                'phone_number': '+256704567890',
                'NIN': 'CM456789012DEFGHI',
                'role': 'mse',
                'email': 'sarah.trader@example.com',
                'category': categories[1],  # producer
                'location': 'Entebbe, Uganda',
                'status': 'approved'
            },
            {
                'username': 'david_merchant',
                'first_name': 'David',
                'last_name': 'Merchant',
                'phone_number': '+256705678901',
                'NIN': 'CM567890123EFGHIJ',
                'role': 'mse',
                'email': 'david.merchant@example.com',
                'category': categories[0],  # input
                'location': 'Masaka, Uganda',
                'status': 'approved'
            }
        ]
        
        for data in sample_data:
            # Create user
            user = User.objects.create_user(
                username=data['username'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone_number=data['phone_number'],
                NIN=data['NIN'],
                role=data['role'],
                email=data['email'],
                password='password123',
                is_approved=True
            )
            
            # Create MSE
            mse = MSE.objects.create(
                owner=user,
                first_name=data['first_name'],
                last_name=data['last_name'],
                nin=data['NIN'],
                phone=data['phone_number'],
                email=data['email'],
                category=data['category'],
                location=data['location'],
                status=data['status']
            )
            
            users_and_mses.append((user, mse))
            self.stdout.write(f'Created user and MSE: {user.username}')
        
        return users_and_mses

    def create_wallets(self, users_and_mses):
        """Create wallets for MSEs"""
        wallets = []
        
        for user, mse in users_and_mses:
            # Random initial balance between 100,000 and 2,000,000 UGX
            initial_balance = Decimal(random.randint(100000, 2000000))
            
            wallet = Wallet.objects.create(
                mse=mse,
                balance=initial_balance,
                currency='UGX'
            )
            
            wallets.append(wallet)
            self.stdout.write(f'Created wallet for {mse.first_name} with balance: {wallet.balance} {wallet.currency}')
        
        return wallets

    def create_groups_and_memberships(self, users_and_mses):
        """Create sample groups and group memberships"""
        groups_and_memberships = []
        
        # Sample group data
        group_data = [
            {
                'name': 'Kampala Farmers Cooperative',
                'description': 'A cooperative of farmers in Kampala region focusing on maize and coffee production'
            },
            {
                'name': 'Jinja Input Suppliers Association',
                'description': 'Association of agricultural input suppliers in Jinja region'
            },
            {
                'name': 'Mukono Processors Union',
                'description': 'Union of agricultural processors in Mukono region'
            },
            {
                'name': 'Entebbe Traders Group',
                'description': 'Group of agricultural traders in Entebbe region'
            }
        ]
        
        for group_info in group_data:
            # Randomly assign creator
            creator_user, creator_mse = random.choice(users_and_mses)
            
            group = Group.objects.create(
                name=group_info['name'],
                description=group_info['description'],
                created_by=creator_user
            )
            
            # Add 2-4 members to each group
            num_members = random.randint(2, 4)
            selected_mses = random.sample(users_and_mses, min(num_members, len(users_and_mses)))
            
            group_memberships = []
            for user, mse in selected_mses:
                membership = GroupMembership.objects.create(
                    group=group,
                    mse=mse,
                    is_active=True
                )
                group_memberships.append(membership)
            
            groups_and_memberships.append((group, group_memberships))
            self.stdout.write(f'Created group: {group.name} with {len(group_memberships)} members')
        
        return groups_and_memberships

    def create_group_wallets(self, groups_and_memberships):
        """Create wallets for groups"""
        group_wallets = []
        
        for group, memberships in groups_and_memberships:
            # Random initial balance between 500,000 and 5,000,000 UGX
            initial_balance = Decimal(random.randint(500000, 5000000))
            
            wallet = GroupWallet.objects.create(
                group=group,
                balance=initial_balance,
                currency='UGX'
            )
            
            group_wallets.append(wallet)
            self.stdout.write(f'Created group wallet for {group.name} with balance: {wallet.balance} {wallet.currency}')
        
        return group_wallets

    def create_loan_products(self):
        """Create sample loan products"""
        loan_products = []
        
        # Sample loan product data
        product_data = [
            {
                'name': 'Agricultural Input Loan',
                'interest_rate': Decimal('12.50'),
                'max_amount': Decimal('5000000.00'),
                'repayment_period_months': 12
            },
            {
                'name': 'Equipment Financing',
                'interest_rate': Decimal('15.00'),
                'max_amount': Decimal('10000000.00'),
                'repayment_period_months': 24
            },
            {
                'name': 'Working Capital Loan',
                'interest_rate': Decimal('18.00'),
                'max_amount': Decimal('3000000.00'),
                'repayment_period_months': 6
            },
            {
                'name': 'Harvest Financing',
                'interest_rate': Decimal('14.50'),
                'max_amount': Decimal('8000000.00'),
                'repayment_period_months': 18
            },
            {
                'name': 'Emergency Loan',
                'interest_rate': Decimal('20.00'),
                'max_amount': Decimal('2000000.00'),
                'repayment_period_months': 3
            }
        ]
        
        for data in product_data:
            product = LoanProduct.objects.create(
                name=data['name'],
                interest_rate=data['interest_rate'],
                max_amount=data['max_amount'],
                repayment_period_months=data['repayment_period_months'],
                is_active=True
            )
            
            loan_products.append(product)
            self.stdout.write(f'Created loan product: {product.name} with {product.interest_rate}% interest')
        
        return loan_products

    def create_group_loans(self, groups_and_memberships, loan_products, users_and_mses):
        """Create sample group loans"""
        group_loans = []
        
        # Generate loans for the last 12 months
        end_date = datetime.now()
        
        for _ in range(15):  # Create 15 sample loans
            # Random group
            group, memberships = random.choice(groups_and_memberships)
            
            # Random loan product
            product = random.choice(loan_products)
            
            # Random amount (within product limits)
            max_amount = product.max_amount
            amount = Decimal(random.randint(500000, int(max_amount)))
            
            # Random status with weighted distribution
            status_weights = {'pending': 0.2, 'approved': 0.3, 'disbursed': 0.3, 'repaid': 0.15, 'rejected': 0.05}
            status = random.choices(list(status_weights.keys()), weights=list(status_weights.values()))[0]
            
            # Random admin user for approval
            admin_user = random.choice(users_and_mses)[0] if status in ['approved', 'disbursed', 'repaid'] else None
            
            # Random dates
            random_days = random.randint(0, 365)
            created_date = end_date - timedelta(days=random_days)
            
            approved_date = None
            disbursed_date = None
            
            if status in ['approved', 'disbursed', 'repaid']:
                approved_date = created_date + timedelta(days=random.randint(1, 30))
            
            if status in ['disbursed', 'repaid']:
                disbursed_date = approved_date + timedelta(days=random.randint(1, 15))
            
            loan = GroupLoan.objects.create(
                group=group,
                product=product,
                amount=amount,
                status=status,
                approved_by=admin_user,
                approved_at=approved_date,
                disbursed_at=disbursed_date,
                created_at=created_date
            )
            
            group_loans.append(loan)
        
        self.stdout.write(f'Created {len(group_loans)} group loans')
        return group_loans

    def create_loan_repayments(self, group_loans):
        """Create sample loan repayments"""
        loan_repayments = []
        
        # Only create repayments for disbursed or repaid loans
        eligible_loans = [loan for loan in group_loans if loan.status in ['disbursed', 'repaid']]
        
        for loan in eligible_loans:
            # Calculate total repayments needed
            total_repayment = loan.amount + (loan.amount * loan.product.interest_rate / 100)
            
            # Create 1-3 repayment installments
            num_repayments = random.randint(1, 3)
            repayment_amount = total_repayment / num_repayments
            
            for i in range(num_repayments):
                # Random repayment date after disbursement
                if loan.disbursed_at:
                    days_after_disbursement = random.randint(30 * (i + 1), 90 * (i + 1))
                    repayment_date = loan.disbursed_at + timedelta(days=days_after_disbursement)
                    
                    repayment = GroupLoanRepayment.objects.create(
                        loan=loan,
                        amount=repayment_amount,
                        repaid_at=repayment_date
                    )
                    
                    loan_repayments.append(repayment)
        
        self.stdout.write(f'Created {len(loan_repayments)} loan repayments')
        return loan_repayments

    def create_products(self, users_and_mses):
        """Create sample products"""
        products = []
        
        # Sample product data
        product_data = [
            {'name': 'Maize Seeds', 'price': Decimal('15000.00'), 'unit': 'kg'},
            {'name': 'Fertilizer NPK', 'price': Decimal('45000.00'), 'unit': '50kg bag'},
            {'name': 'Pesticides', 'price': Decimal('25000.00'), 'unit': 'liter'},
            {'name': 'Irrigation Pipes', 'price': Decimal('150000.00'), 'unit': 'meter'},
            {'name': 'Garden Tools', 'price': Decimal('35000.00'), 'unit': 'set'},
            {'name': 'Fresh Tomatoes', 'price': Decimal('3000.00'), 'unit': 'kg'},
            {'name': 'Green Beans', 'price': Decimal('4000.00'), 'unit': 'kg'},
            {'name': 'Sweet Potatoes', 'price': Decimal('2000.00'), 'unit': 'kg'},
            {'name': 'Cassava', 'price': Decimal('1500.00'), 'unit': 'kg'},
            {'name': 'Coffee Beans', 'price': Decimal('8000.00'), 'unit': 'kg'},
            {'name': 'Tea Leaves', 'price': Decimal('5000.00'), 'unit': 'kg'},
            {'name': 'Bananas', 'price': Decimal('2500.00'), 'unit': 'bunch'},
        ]
        
        for data in product_data:
            # Randomly assign product to an MSE
            user, mse = random.choice(users_and_mses)
            
            product = Product.objects.create(
                mse=mse,
                name=data['name'],
                price=data['price'],
                unit=data['unit']
            )
            
            products.append(product)
            self.stdout.write(f'Created product: {product.name} at {product.price} UGX per {product.unit}')
        
        return products

    def create_customers(self, users_and_mses):
        """Create sample customers"""
        customers = []
        
        # Sample customer data
        customer_data = [
            {'name': 'Alice Johnson', 'phone_number': '+256711111111'},
            {'name': 'Bob Smith', 'phone_number': '+256722222222'},
            {'name': 'Carol Davis', 'phone_number': '+256733333333'},
            {'name': 'Daniel Wilson', 'phone_number': '+256744444444'},
            {'name': 'Emma Brown', 'phone_number': '+256755555555'},
            {'name': 'Frank Miller', 'phone_number': '+256766666666'},
            {'name': 'Grace Taylor', 'phone_number': '+256777777777'},
            {'name': 'Henry Anderson', 'phone_number': '+256788888888'},
        ]
        
        for data in customer_data:
            # Randomly assign customer to an MSE
            user, mse = random.choice(users_and_mses)
            
            customer = Customer.objects.create(
                mse=mse,
                name=data['name'],
                phone_number=data['phone_number']
            )
            
            customers.append(customer)
            self.stdout.write(f'Created customer: {customer.name} for {mse.first_name}')
        
        return customers

    def create_suppliers(self, users_and_mses):
        """Create sample suppliers"""
        suppliers = []
        
        # Sample supplier data
        supplier_data = [
            {'name': 'Agro Supply Co.', 'phone_number': '+256791111111'},
            {'name': 'Farm Tools Ltd.', 'phone_number': '+256792222222'},
            {'name': 'Seed Bank Uganda', 'phone_number': '+256793333333'},
            {'name': 'Chemical Solutions', 'phone_number': '+256794444444'},
            {'name': 'Irrigation Systems', 'phone_number': '+256795555555'},
            {'name': 'Organic Fertilizers', 'phone_number': '+256796666666'},
        ]
        
        for data in supplier_data:
            # Randomly assign supplier to an MSE
            user, mse = random.choice(users_and_mses)
            
            supplier = Supplier.objects.create(
                mse=mse,
                name=data['name'],
                phone_number=data['phone_number']
            )
            
            suppliers.append(supplier)
            self.stdout.write(f'Created supplier: {supplier.name} for {mse.first_name}')
        
        return suppliers

    def create_transactions(self, users_and_mses, products, customers, suppliers):
        """Create sample transactions"""
        transactions = []
        
        # Generate transactions for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        for _ in range(50):  # Create 50 sample transactions
            # Random transaction type
            transaction_type = random.choice(['purchase', 'sale'])
            
            # Random MSE
            user, mse = random.choice(users_and_mses)
            
            # Random product
            product = random.choice(products)
            
            # Random counterparty
            if transaction_type == 'purchase':
                counterparty = random.choice(suppliers)
                counterparty_name = counterparty.name
            else:
                counterparty = random.choice(customers)
                counterparty_name = counterparty.name
            
            # Random quantity and amount
            quantity = Decimal(random.randint(1, 100))
            amount = product.price * quantity
            
            # Random date within last 30 days
            random_days = random.randint(0, 30)
            random_date = end_date - timedelta(days=random_days)
            
            transaction = Transaction.objects.create(
                mse=mse,
                type=transaction_type,
                product=product,
                counterparty_name=counterparty_name,
                amount=amount,
                quantity=quantity,
                created_at=random_date
            )
            
            transactions.append(transaction)
        
        self.stdout.write(f'Created {len(transactions)} transactions')
        return transactions

    def create_notifications(self, users_and_mses):
        """Create sample notifications"""
        notifications = []
        
        # Sample notification messages
        notification_messages = [
            'New product available: Fresh tomatoes at great prices!',
            'Your order has been confirmed and is being processed.',
            'Payment received for your recent sale.',
            'New customer inquiry about your products.',
            'Price update: Fertilizer prices have increased by 10%.',
            'Your account has been successfully verified.',
            'New supplier registered in your area.',
            'Market trends: High demand for organic products.',
            'Weather alert: Prepare for upcoming rainy season.',
            'Your wallet balance has been updated.',
        ]
        
        for _ in range(30):  # Create 30 sample notifications
            # Random MSE
            user, mse = random.choice(users_and_mses)
            
            # Random message
            message = random.choice(notification_messages)
            
            # Random read status
            is_read = random.choice([True, False])
            
            # Random date within last 7 days
            random_days = random.randint(0, 7)
            random_date = datetime.now() - timedelta(days=random_days)
            
            notification = Notification.objects.create(
                mse=mse,
                message=message,
                is_read=is_read,
                created_at=random_date
            )
            
            notifications.append(notification)
        
        self.stdout.write(f'Created {len(notifications)} notifications')
        return notifications
