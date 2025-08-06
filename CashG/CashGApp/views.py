from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
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
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')


@login_required
def dashboard(request):
    try:
        account = Account.objects.get(user=request.user)
        recent_transactions = Transaction.objects.filter(account=account).order_by('-timestamp')[:5]
    except Account.DoesNotExist:
        messages.error(request, "Account not found. Please contact support.")
        return redirect('login')
    
    context = {
        'account': account,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'dashboard.html', context)


@csrf_protect
@transaction.atomic
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        account_type = request.POST.get('account_type')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not all([username, account_type, password, confirm_password]):
            messages.error(request, "All fields are required.")
            return render(request, 'sign_up.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'sign_up.html')

        if account_type not in ['Admin', 'Client']:
            messages.error(request, "Invalid account type selected.")
            return render(request, 'sign_up.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'sign_up.html')

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'sign_up.html')

        try:
            user = User.objects.create_user(username=username, password=password)
            Profile.objects.create(user=user, account_type=account_type)
            
            # Create account for the user
            Account.objects.create(
                user=user,
                account_type='SAVINGS' if account_type == 'Client' else 'CHECKING'
            )
            
            messages.success(request, "Account created successfully. You can now login.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return render(request, 'sign_up.html')

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
                        transaction_type='DEPOSIT',
                        description=f'Deposit to {account.account_type} account'
                    )
                messages.success(request, f"Successfully deposited ₱{amount:,.2f}.")
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
                        transaction_type='WITHDRAWAL',
                        description=f'Withdrawal from {account.account_type} account'
                    )
                messages.success(request, f"Successfully withdrew ₱{amount:,.2f}.")
                return redirect('dashboard')
            else:
                messages.error(request, "Withdrawal must be between ₱200 and ₱50,000.")
        except (ValueError, TypeError, Decimal.InvalidOperation):
            messages.error(request, "Invalid amount format.")

    return render(request, 'withdraw.html', {'account': account})


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
            return render(request, 'transfer.html', {'account': account})

        try:
            recipient_user = User.objects.get(username=recipient_username)
            recipient_account = Account.objects.select_for_update().get(user=recipient_user)
        except User.DoesNotExist:
            messages.error(request, "Recipient user not found.")
            return render(request, 'transfer.html', {'account': account})
        except Account.DoesNotExist:
            messages.error(request, "Recipient account not found.")
            return render(request, 'transfer.html', {'account': account})

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
                    description=f'Transfer to {recipient_username}: {note}' if note else f'Transfer to {recipient_username}',
                    transaction_type='TRANSFER'
                )

                Transaction.objects.create(
                    account=recipient_account,
                    amount=amount,
                    description=f'Received from {request.user.username}: {note}' if note else f'Received from {request.user.username}',
                    transaction_type='RECEIVED'
                )

                Transfer.objects.create(
                    sender_account=account,
                    recipient_account=recipient_account,
                    amount=amount,
                    note=note
                )

            messages.success(request, f"Successfully transferred ₱{amount:,.2f} to {recipient_username}.")
            return redirect('dashboard')

    return render(request, 'transfer.html', {'account': account})


@login_required
def history(request):
    try:
        account = Account.objects.get(user=request.user)
        transactions = Transaction.objects.filter(account=account).order_by('-timestamp')
    except Account.DoesNotExist:
        messages.error(request, "Account not found.")
        return redirect('dashboard')

    context = {
        'account': account,
        'transactions': transactions,
    }
    return render(request, 'transactions.html', context)


@login_required
def profile(request):
    try:
        account = Account.objects.get(user=request.user)
        user_profile = Profile.objects.get(user=request.user)
    except (Account.DoesNotExist, Profile.DoesNotExist):
        messages.error(request, "Profile not found.")
        return redirect('dashboard')

    if request.method == 'POST':
        # Handle profile updates here if needed
        messages.success(request, "Profile updated successfully.")
        return redirect('profile')

    context = {
        'account': account,
        'profile': user_profile,
    }
    return render(request, 'profile.html', context)
