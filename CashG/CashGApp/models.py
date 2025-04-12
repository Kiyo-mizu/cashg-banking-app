from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Account(models.Model):
    ACCOUNT_TYPE = [('SAVINGS','Savings'),
                    ('CHECKING','Checking'),]
    
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name='account')
    account_number = models.CharField(max_length=255, unique=True)
    account_type = models.CharField(max_length=255,choices=ACCOUNT_TYPE)
    balance = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.account_number}'
    
class Transaction(models.Model):
    TRANSACTION_TYPE = [
        ('DEPOSIT','Deposit'),
        ('WITHDRAWAL','Withdrawal'),
        ('TRANSFER','Transfer')
    ]

    account = models.ForeignKey(Account,on_delete=models.CASCADE,related_name='transactions')
    transaction_type = models.CharField(max_length=255,choices=TRANSACTION_TYPE)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f'{self.transaction_type} of {self.amount} on {self.timestamp}'
    
class Transfer(models.Model):
    sender_account = models.ForeignKey(Account, on_delete=models.CASCADE,related_name='sent_transfers')
    recipient_account = models.ForeignKey(Account, on_delete=models.CASCADE,related_name='received_transfers')
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return f'Transfer from {self.sender_account} to {self.recipient_account} with the amount of {self.amount}'




    