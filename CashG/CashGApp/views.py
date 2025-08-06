from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import *
from decimal import Decimal
from django.contrib.auth.models import User 
from django.contrib.auth.decorators import login_required  
from django.db import transaction
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

@login_required
def Dashboard(request):
    try:
        account = Account.objects.get(user=request.user)
    except Account.DoesNotExist:
        messages.error(request, "Account not found. Please contact support.")
        return redirect('login')
    
    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')[:5]
    return render(request, 'dashboard.html', {'account': account, 'transactions': transactions})

@login_required 
def deposit(request):
    try:
        account = Account.objects.get(user=request.user)
    except Account.DoesNotExist:
        messages.error(request, "Account not found.")
        return redirect('dashboard')

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

@login_required
def withdraw(request):
    try:
        account = Account.objects.get(user=request.user)
    except Account.DoesNotExist:
        messages.error(request, "Account not found.")
        return redirect('dashboard')
        
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

@login_required
def transfer(request):
    try:
        account = Account.objects.get(user=request.user)
    except Account.DoesNotExist:
        messages.error(request, "Account not found.")
        return redirect('dashboard')

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

@login_required
def history(request):
    try:
        account = Account.objects.get(user=request.user)
    except Account.DoesNotExist:
        messages.error(request, "Account not found.")
        return redirect('dashboard')
        
    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')[:10]
    return render(request, 'transactions.html', {'transactions': transactions})

@transaction.atomic
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        account_type = request.POST.get('account_type')

        # Validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already in use.')
        else:
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1
                )
                
                # Generate unique account number
                while True:
                    num_size = 12
                    generated_number = []
                    for i in range(num_size):
                        generated_number.append(random.randint(0, 9))
                    
                    new_account_number = ''.join(str(digit) for digit in generated_number)
                    formatted_account_number = f'{new_account_number[0:4]}-{new_account_number[4:8]}-{new_account_number[8:]}'
                    
                    # Check if account number already exists
                    if not Account.objects.filter(account_number=formatted_account_number).exists():
                        break
                
                # Create account with all required fields
                Account.objects.create(
                    user=user,
                    account_number=formatted_account_number,
                    account_type=account_type,
                    balance=Decimal('0.00')  # Use Decimal explicitly
                )
                
                messages.success(request, 'Account created successfully! Please login.')
                return redirect('login')
                
            except Exception as e:
                # The @transaction.atomic decorator will automatically rollback if there's an error
                messages.error(request, f'Account creation failed. Please try again. Error: {str(e)}')
                print(f"Signup error: {str(e)}")  # This will show in logs

    return render(request, 'sign_up.html')
