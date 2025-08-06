from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import random
import string

# Create your models here.

class Profile(models.Model):
    ACCOUNT_TYPE = [
        ('Admin', 'Admin'),
        ('Client', 'Client'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE, default='Client')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} - {self.account_type}'

class Account(models.Model):
    ACCOUNT_TYPE = [
        ('SAVINGS', 'Savings'),
        ('CHECKING', 'Checking'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    account_number = models.CharField(max_length=255, unique=True)
    account_type = models.CharField(max_length=255, choices=ACCOUNT_TYPE, default='SAVINGS')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} - {self.account_number}'
    
    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = self.generate_account_number()
        super().save(*args, **kwargs)
    
    def generate_account_number(self):
        """Generate a unique 10-digit account number"""
        while True:
            account_number = ''.join(random.choices(string.digits, k=10))
            if not Account.objects.filter(account_number=account_number).exists():
                return account_number
    
    def can_withdraw(self, amount):
        """Check if account has sufficient balance for withdrawal"""
        return self.balance >= amount and self.is_active
    
    def can_transfer(self, amount):
        """Check if account can transfer the specified amount"""
        return self.can_withdraw(amount) and 200 <= amount <= 50000

class Transaction(models.Model):
    TRANSACTION_TYPE = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('TRANSFER', 'Transfer'),
        ('RECEIVED', 'Received'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=255, choices=TRANSACTION_TYPE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    reference_number = models.CharField(max_length=50, unique=True, blank=True)

    def __str__(self):
        return f'{self.transaction_type} of ₱{self.amount} on {self.timestamp}'
    
    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = self.generate_reference_number()
        super().save(*args, **kwargs)
    
    def generate_reference_number(self):
        """Generate a unique reference number"""
        while True:
            ref_number = f"TXN{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
            if not Transaction.objects.filter(reference_number=ref_number).exists():
                return ref_number

class Transfer(models.Model):
    sender_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='sent_transfers')
    recipient_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='received_transfers')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('200.00')), MaxValueValidator(Decimal('50000.00'))])
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
    transfer_id = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=[('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')], default='COMPLETED')

    def __str__(self):
        return f'Transfer {self.transfer_id}: ₱{self.amount} from {self.sender_account.user.username} to {self.recipient_account.user.username}'
    
    def save(self, *args, **kwargs):
        if not self.transfer_id:
            self.transfer_id = self.generate_transfer_id()
        super().save(*args, **kwargs)
    
    def generate_transfer_id(self):
        """Generate a unique transfer ID"""
        while True:
            transfer_id = f"TRF{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}"
            if not Transfer.objects.filter(transfer_id=transfer_id).exists():
                return transfer_id
    



    