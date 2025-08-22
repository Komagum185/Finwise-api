from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.hashers import make_password
from decimal import Decimal
from django.contrib.auth import get_user_model
from .models import USSDUser, Wallet, Product, Contact, Loan, USSDSession

User = get_user_model()


class USSDAPITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.url = reverse('ussd-entry')
		self.msisdn = '+256700000001'
		self.sessionId = 'sess1'

	def post(self, text):
		return self.client.post(self.url, {"msisdn": self.msisdn, "sessionId": self.sessionId, "text": text}, format='json')

	def test_login_and_menu(self):
		# Create verified user in main system
		main_user = User.objects.create_user(
			username='testuser',
			phone_number=self.msisdn,
			ussd_enabled=True,
			status='active'
		)
		
		# First request prompts for PIN
		resp = self.post("")
		self.assertEqual(resp.status_code, 200)
		self.assertIn('CON', resp.content.decode())

		# Enter PIN – should set PIN and show menu
		resp = self.post("1234")
		self.assertEqual(resp.status_code, 200)
		self.assertIn('CON', resp.content.decode())
		self.assertTrue(USSDUser.objects.filter(phone=self.msisdn).exists())
		
		# Verify PIN was set in main user
		main_user.refresh_from_db()
		self.assertTrue(main_user.ussd_pin_hash)
	
	def test_unregistered_user_rejected(self):
		"""Test that unregistered users are rejected"""
		# First request prompts for PIN
		resp = self.post("")
		self.assertEqual(resp.status_code, 200)
		self.assertIn('CON', resp.content.decode())

		# Enter PIN - should be rejected
		resp = self.post("1234")
		self.assertEqual(resp.status_code, 200)
		self.assertIn('END Phone not registered', resp.content.decode())
		self.assertFalse(USSDUser.objects.filter(phone=self.msisdn).exists())
	
	def test_disabled_ussd_user_rejected(self):
		"""Test that users with ussd_enabled=False are rejected"""
		# Create user but disable USSD
		main_user = User.objects.create_user(
			username='testuser',
			phone_number=self.msisdn,
			ussd_enabled=False,
			status='active'
		)
		
		# First request prompts for PIN
		resp = self.post("")
		self.assertEqual(resp.status_code, 200)
		self.assertIn('CON', resp.content.decode())

		# Enter PIN - should be rejected
		resp = self.post("1234")
		self.assertEqual(resp.status_code, 200)
		self.assertIn('END Phone not registered', resp.content.decode())

	def test_deposit_and_balance(self):
		# Create verified user in main system
		main_user = User.objects.create_user(
			username='testuser',
			phone_number=self.msisdn,
			ussd_enabled=True,
			status='active',
			ussd_pin_hash=make_password('1234')
		)
		ussd_user = USSDUser.objects.create(name='u', phone=self.msisdn, pin_hash=make_password('1234'))
		Wallet.objects.create(owner=ussd_user)
		# Login
		self.post("")
		self.post("1234")
		# Deposit 1000
		resp = self.post("2")
		self.assertIn('CON', resp.content.decode())
		resp = self.post("2*1000")
		self.assertIn('END', resp.content.decode())
		wallet = Wallet.objects.get(owner=ussd_user)
		self.assertEqual(wallet.balance, Decimal('1000'))
		# Check balance
		# New session for simplicity
		self.sessionId = 'sess2'
		self.post("")
		self.post("1234")
		resp = self.post("6")
		self.assertIn('END Balance', resp.content.decode())

	def test_withdraw_insufficient_and_success(self):
		# Create verified user in main system
		main_user = User.objects.create_user(
			username='testuser',
			phone_number=self.msisdn,
			ussd_enabled=True,
			status='active',
			ussd_pin_hash=make_password('1234')
		)
		ussd_user = USSDUser.objects.create(name='u', phone=self.msisdn, pin_hash=make_password('1234'))
		Wallet.objects.create(owner=ussd_user, balance=Decimal('500'))
		self.post("")
		self.post("1234")
		resp = self.post("3*600")
		self.assertIn('Insufficient', resp.content.decode())
		resp = self.post("3*200")
		self.assertIn('Withdrawal successful', resp.content.decode())

	def test_buy_product_flow(self):
		# Create verified user in main system
		main_user = User.objects.create_user(
			username='testuser',
			phone_number=self.msisdn,
			ussd_enabled=True,
			status='active',
			ussd_pin_hash=make_password('1234')
		)
		ussd_user = USSDUser.objects.create(name='u', phone=self.msisdn, pin_hash=make_password('1234'))
		wallet = Wallet.objects.create(owner=ussd_user, balance=Decimal('1000'))
		p = Product.objects.create(owner=ussd_user, name='Item', price=Decimal('100'), stock=10)
		self.post("")
		self.post("1234")
		# List products
		resp = self.post("1")
		self.assertIn('CON Select product ID', resp.content.decode())
		# Choose product and quantity 2
		resp = self.post(f"1*{p.id}")
		self.assertIn('Enter quantity', resp.content.decode())
		resp = self.post(f"1*{p.id}*2")
		self.assertIn('Purchase successful', resp.content.decode())
		wallet.refresh_from_db()
		self.assertEqual(wallet.balance, Decimal('800'))

	def test_request_loan(self):
		# Create verified user in main system
		main_user = User.objects.create_user(
			username='testuser',
			phone_number=self.msisdn,
			ussd_enabled=True,
			status='active',
			ussd_pin_hash=make_password('1234')
		)
		ussd_user = USSDUser.objects.create(name='u', phone=self.msisdn, pin_hash=make_password('1234'))
		Wallet.objects.create(owner=ussd_user)
		self.post("")
		self.post("1234")
		resp = self.post("4*500")
		self.assertIn('Loan request submitted', resp.content.decode())
		self.assertEqual(Loan.objects.filter(borrower=ussd_user).count(), 1)

	def test_contacts_add_and_list(self):
		# Create verified user in main system
		main_user = User.objects.create_user(
			username='testuser',
			phone_number=self.msisdn,
			ussd_enabled=True,
			status='active',
			ussd_pin_hash=make_password('1234')
		)
		ussd_user = USSDUser.objects.create(name='u', phone=self.msisdn, pin_hash=make_password('1234'))
		Wallet.objects.create(owner=ussd_user)
		self.post("")
		self.post("1234")
		resp = self.post("5")
		self.assertIn('Add Contact', resp.content.decode())
		resp = self.post("5*1")
		self.assertIn('Enter name', resp.content.decode())
		resp = self.post("5*1*Alice")
		self.assertIn('Enter phone', resp.content.decode())
		resp = self.post("5*1*Alice*0700")
		self.assertIn('Contact added', resp.content.decode())
		# View contacts
		self.sessionId = 'sess3'
		self.post("")
		self.post("1234")
		resp = self.post("5*2")
		self.assertIn('Contacts:', resp.content.decode())
