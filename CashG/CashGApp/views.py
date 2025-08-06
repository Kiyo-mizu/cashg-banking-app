from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import *
from decimal import Decimal
from django.contrib.auth.models import User 
from django.contrib.auth.decorators import login_required  
from django.db import transaction
import random

from django.views.decorators.csrf import csrf_protect


@csrf_protect
def Login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'login.html')

        user = authenticate(request, username=username.strip(), password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Oops! The username or password you entered is incorrect.')

    return render(request, 'login.html')


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')
    
@csrf_protect
@transaction.atomic
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        account_type = request.POST.get('account_type')

        # Validation
        if not username or not email or not password1 or not password2:
            messages.error(request, 'All fields are required.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already in use.')
        else:
            try:
                user = User.objects.create_user(
                    username=username.strip(),
                    email=email.strip(),
                    password=password1
                )
                # Generate unique account number
                while True:
                    new_account_number = ''.join([str(random.randint(0, 9)) for _ in range(12)])
                    formatted_account_number = f'{new_account_number[:4]}-{new_account_number[4:8]}-{new_account_number[8:]}'
                    if not Account.objects.filter(account_number=formatted_account_number).exists():
                        break

                Account.objects.create(
                    user=user,
                    account_number=formatted_account_number,
                    account_type=account_type,
                    balance=Decimal('0.00')
                )

                messages.success(request, 'Account created successfully! Please login.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Account creation failed. Please try again.')
                print(f"Signup error: {str(e)}")

    return render(request, 'sign_up.html')

@login_required
@csrf_protect
def deposit(request):
    try:
        account = Account.objects.select_for_update().get(user=request.user)
    except Account.DoesNotExist:
        messages.error(request, "Account not found.")
        return redirect('dashboard')

    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        try:
            amount = Decimal(amount_str)
            if amount >= 1.00:
                with transaction.atomic():
                    account.balance += amount
                    account.save()
                    Transaction.objects.create(
                        account=account,
                        amount=amount,
                        transaction_type='DEPOSIT'
                    )
                messages.success(request, f"Successfully deposited ₱{amount}.")
                return redirect('dashboard')
            else:
                messages.error(request, "Amount must be at least ₱1.")
        except (ValueError, TypeError, Decimal.InvalidOperation):
            messages.error(request, "Invalid amount format.")

    return render(request, 'deposit.html', {'account': account})

@login_required
@csrf_protect
def withdraw(request):
    try:
        account = Account.objects.select_for_update().get(user=request.user)
    except Account.DoesNotExist:
        messages.error(request, "Account not found.")
        return redirect('dashboard')

    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        try:
            amount = Decimal(amount_str)
            if amount > account.balance:
                messages.error(request, "Insufficient balance.")
            elif 200.00 <= amount <= 50000.00:
                with transaction.atomic():
                    account.balance -= amount
                    account.save()
                    Transaction.objects.create(
                        account=account,
                        amount=amount,
                        transaction_type='WITHDRAWAL'
                    )
                messages.success(request, f"Successfully withdrew ₱{amount}.")
                return redirect('dashboard')
            else:
                messages.error(request, "Withdrawal must be between ₱200 and ₱50,000.")
        except (ValueError, TypeError, Decimal.InvalidOperation):
            messages.error(request, "Invalid amount format.")

    return render(request, 'withdraw.html')

@login_required
@csrf_protect
def transfer(request):
    try:
        account = Account.objects.select_for_update().get(user=request.user)
    except Account.DoesNotExist:
        messages.error(request, "Account not found.")
        return redirect('dashboard')

    if request.method == 'POST':
        recipient_username = request.POST.get('recipient')
        amount_str = request.POST.get('amount')
        note = request.POST.get('note', '')

        try:
            amount = Decimal(amount_str)
        except (ValueError, TypeError, Decimal.InvalidOperation):
            messages.error(request, "Invalid amount.")
            return render(request, 'transfer.html')

        try:
            recipient_user = User.objects.get(username=recipient_username)
            recipient_account = Account.objects.select_for_update().get(user=recipient_user)
        except User.DoesNotExist:
            messages.error(request, "Recipient user not found.")
            return render(request, 'transfer.html')
        except Account.DoesNotExist:
            messages.error(request, "Recipient account not found.")
            return render(request, 'transfer.html')

        if recipient_user == request.user:
            messages.error(request, "Cannot transfer to your own account.")
        elif amount > account.balance:
            messages.error(request, "Insufficient balance.")
        elif not (200 <= amount <= 50000):
            messages.error(request, "Transfer amount must be between ₱200 and ₱50,000.")
        else:
            with transaction.atomic():
                account.balance -= amount
                recipient_account.balance += amount
                account.save()
                recipient_account.save()

                Transaction.objects.create(
                    account=account,
                    amount=amount,
                    description=note,
                    transaction_type='TRANSFER'
                )

                Transaction.objects.create(
                    account=recipient_account,
                    amount=amount,
                    description=note,
                    transaction_type='RECEIVED'
                )

                Transfer.objects.create(
                    sender_account=account,
                    recipient_account=recipient_account,
                    amount=amount,
                    note=note
                )

            messages.success(request, f"Successfully transferred ₱{amount} to {recipient_username}.")
            return redirect('dashboard')

    return render(request, 'transfer.html')
    
@login_required
def history(request):
    try:
        account = Account.objects.get(user=request.user)
    except Account.DoesNotExist:
        messages.error(request, "Account not found.")
        return redirect('dashboard')
        
    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')[:10]
    return render(request, 'transactions.html', {'transactions': transactions})
