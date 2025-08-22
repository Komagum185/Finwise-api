from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from decimal import Decimal

User = get_user_model()

# -------------------------
# Validators
# -------------------------
phone_regex = RegexValidator(
    regex=r'^(?:070|074|075|\+256|256)\d{6,9}$',
    message="Phone number must start with 070, 074, 075, +256, or 256 and contain 9-12 digits total."
)

# -------------------------
# USSD User
# -------------------------
class USSDUser(models.Model):
    phone = models.CharField(max_length=15, unique=True, validators=[phone_regex])
    name = models.CharField(max_length=255)
    pin_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    ussd_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"



class USSDSession(models.Model):
    msisdn = models.CharField(max_length=15, validators=[phone_regex])
    session_id = models.CharField(max_length=255)
    current_step = models.CharField(max_length=50, default='login')
    state_data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # rename here

    def has_timed_out(self):
        from django.utils import timezone
        import datetime
        timeout_minutes = 5
        return (timezone.now() - self.updated_at) > datetime.timedelta(minutes=timeout_minutes)

    def __str__(self):
        return f"Session {self.session_id} for {self.msisdn}"

# -------------------------
# Wallet
# -------------------------
class Wallet(models.Model):
    owner = models.OneToOneField(USSDUser, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wallet: {self.owner.name} - {self.balance}"

# Wallet Audit Log
# -------------------------
class WalletAuditLog(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=[
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('purchase', 'Purchase'),
        ('loan_request', 'Loan Request')
    ])
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_before = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    reference = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - {self.amount} (Wallet: {self.wallet.owner.name})"

# -------------------------
# Transaction
# -------------------------
class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    type = models.CharField(max_length=20, choices=[('deposit','Deposit'),('withdrawal','Withdrawal'),('purchase','Purchase')])
    reference = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('pending','Pending'),('completed','Completed'),('failed','Failed')], default='completed')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.amount} ({self.status})"


# -------------------------
# Product
# -------------------------
class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    owner = models.ForeignKey(USSDUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# -------------------------
# Loan
# -------------------------
class Loan(models.Model):
    borrower = models.ForeignKey(USSDUser, on_delete=models.CASCADE)
    amount_requested = models.DecimalField(max_digits=15, decimal_places=2)
    amount_approved = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=[('pending','Pending'),('approved','Approved'),('declined','Declined')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Loan ({self.borrower.name}) - {self.amount_requested}"


# -------------------------
# Contact
# -------------------------
class Contact(models.Model):
    owner = models.ForeignKey(USSDUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, validators=[phone_regex])
    relationship_type = models.CharField(max_length=50, choices=[('customer','Customer'),('supplier','Supplier')], default='customer')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"


# -------------------------
# USSD Menu
# -------------------------
class USSDMenu(models.Model):
    code = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='submenus')
    is_terminal = models.BooleanField(default=False)
    action = models.CharField(max_length=50, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.code} - {self.title}"
