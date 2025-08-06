from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import *
from decimal import Decimal
from django.contrib.auth.models import User 
from django.contrib.auth.decorators import login_required  
import random

def Login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Oops! The username or password you entered is incorrect.')
            return render(request, 'login.html')

    return render(request, 'login.html')


def Dashboard(request):
    account = Account.objects.get(user=request.user)
    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')[:5]
    return render(request, 'dashboard.html', {'account': account, 'transactions': transactions})

@login_required 
def deposit(request):
    account = Account.objects.get(user=request.user)

    if request.method == 'POST':
        amount_str = request.POST.get('amount')

        try:
            amount = Decimal(amount_str)
            if amount >= 1.00:
                account.balance += amount
                account.save()

                Transaction.objects.create(
                    account=account,
                    amount=amount,
                    transaction_type='DEPOSIT'
                )
                return redirect('dashboard')
            else:
                messages.error(request, "Please enter an amount greater than ₱0.")
        except:
            messages.error(request, "Invalid input. Please enter a valid numeric amount.")
    return render(request, 'deposit.html', {'account': account})


def withdraw(request):
    account = Account.objects.get(user=request.user)
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        try:
            amount = Decimal(amount_str)

            if amount > account.balance:
                messages.error(request, 'Sorry! You have insufficient balance for this withdrawal.')

            elif 200.00 <= amount <= 50000.00:
                account.balance -= amount
                account.save()

                Transaction.objects.create(
                    account=account,
                    amount=amount,
                    transaction_type='WITHDRAW'
                )
                return redirect('dashboard')
            else:
                messages.error(request, "Withdrawal failed. Amount must be between ₱200 and ₱50,000.")

        except:
            messages.error(request, 'Invalid input. Please enter a valid numeric amount.')

    return render(request, 'withdraw.html')


def transfer(request):
    account = Account.objects.get(user=request.user)

    if request.method == 'POST':
        recipient_username = request.POST.get('recipient')
        amount_str = request.POST.get('amount')
        note = request.POST.get('note')
        try:
            amount = Decimal(amount_str)
        except:
            messages.error(request, 'Invalid input. Please enter a valid amount.')
            return render(request, 'transfer.html')

        try:
            recipient_user = User.objects.get(username=recipient_username)
            recipient_account = Account.objects.get(user=recipient_user)
        except:
            messages.error(request, 'Recipient account not found. Please check the username and try again.')
            return render(request, 'transfer.html')
        if account.user == recipient_account.user:
            messages.error(request,'You cant transfer to yourself')
        else:
            if amount > account.balance:
                messages.error(request, "You don't have enough balance to complete this transfer.")
            elif amount < 200 or amount > 50000:
                messages.error(request, "Transfer amount must be between ₱200 and ₱50,000.")
            else:
                account.balance -= amount
                account.save()

                recipient_account.balance += amount
                recipient_account.save()

                Transaction.objects.create(
                    account=account,
                    amount=amount,
                    description = note,
                    transaction_type='TRANSFER'
                )

                Transaction.objects.create(
                    account=recipient_account,
                    amount=amount,
                    description=note,
                    transaction_type='RECEIVED'
                )

                return redirect('dashboard')

    return render(request, 'transfer.html')


def history(request):
    account = Account.objects.get(user=request.user)
    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')[:10]
    return render(request, 'transactions.html', {'transactions': transactions})




def signup(request):
    if request.method == 'POST':
        num_size = 12
        generated_number = []
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        account_type = request.POST.get('account_type')

        for i in range(num_size):
            generated_number.append(random.randint(0,9))
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already in use.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            new_account_number = ''.join(str(digit) for digit in generated_number)

            Account.objects.create(user=user,account_number = f'{new_account_number[0:4]}-{new_account_number[4:8]}-{new_account_number[8:]}',account_type = account_type , balance=0)
            return redirect('login')

    return render(request, 'sign_up.html')
