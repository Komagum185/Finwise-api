from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from .models import Category, Transaction, Budget, Goal
from mses_new.models import MSE, Wallet

User = get_user_model()


class WalletAppTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.mse = MSE.objects.create(
            user=self.user,
            name='Test MSE',
            mse_type='micro'
        )
        
        self.wallet = Wallet.objects.create(
            mse=self.mse,
            name='Test Wallet',
            wallet_type='cash',
            balance=Decimal('1000.00')
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            category_type='expense',
            color='#ff0000'
        )

    def test_category_creation(self):
        """Test category creation"""
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.category_type, 'expense')
        self.assertTrue(self.category.is_active)

    def test_transaction_creation(self):
        """Test transaction creation"""
        transaction = Transaction.objects.create(
            user=self.user,
            title='Test Transaction',
            amount=Decimal('100.00'),
            transaction_type='expense',
            category=self.category,
            transaction_date=timezone.now(),
            wallet=self.wallet
        )
        
        self.assertEqual(transaction.title, 'Test Transaction')
        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.transaction_type, 'expense')

    def test_budget_creation(self):
        """Test budget creation"""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)
        
        budget = Budget.objects.create(
            user=self.user,
            name='Test Budget',
            total_amount=Decimal('1000.00'),
            start_date=start_date,
            end_date=end_date
        )
        
        self.assertEqual(budget.name, 'Test Budget')
        self.assertEqual(budget.total_amount, Decimal('1000.00'))
        self.assertEqual(budget.remaining_amount, Decimal('1000.00'))

    def test_goal_creation(self):
        """Test goal creation"""
        target_date = date.today() + timedelta(days=90)
        
        goal = Goal.objects.create(
            user=self.user,
            name='Test Goal',
            goal_type='savings',
            target_amount=Decimal('5000.00'),
            target_date=target_date
        )
        
        self.assertEqual(goal.name, 'Test Goal')
        self.assertEqual(goal.target_amount, Decimal('5000.00'))
        self.assertEqual(goal.progress_percentage, Decimal('0.00'))

    def test_transaction_validation(self):
        """Test transaction validation"""
        with self.assertRaises(Exception):
            Transaction.objects.create(
                user=self.user,
                title='Invalid Transaction',
                amount=Decimal('-100.00'),  # Negative amount should fail
                transaction_type='expense',
                transaction_date=timezone.now()
            )

    def test_budget_validation(self):
        """Test budget validation"""
        start_date = date.today()
        end_date = start_date - timedelta(days=1)  # End date before start date
        
        with self.assertRaises(Exception):
            Budget.objects.create(
                user=self.user,
                name='Invalid Budget',
                total_amount=Decimal('1000.00'),
                start_date=start_date,
                end_date=end_date
            )

    def test_goal_progress_update(self):
        """Test goal progress update"""
        target_date = date.today() + timedelta(days=90)
        
        goal = Goal.objects.create(
            user=self.user,
            name='Test Goal',
            goal_type='savings',
            target_amount=Decimal('1000.00'),
            target_date=target_date
        )
        
        # Update progress
        goal.current_amount = Decimal('500.00')
        goal.save()
        
        self.assertEqual(goal.progress_percentage, Decimal('50.00'))
        self.assertEqual(goal.remaining_amount, Decimal('500.00'))

