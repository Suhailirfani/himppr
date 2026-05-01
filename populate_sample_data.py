import os
import django
import random
from datetime import date, timedelta
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'himppr_erp.settings')
django.setup()

from django.contrib.auth import get_user_model
from homes.models import Home, Student
from finance.models import AccountCategory, FeeStructure, SpecialProgram, Transaction, Invoice

User = get_user_model()

def populate():
    print("Populating sample data...")
    
    # 1. Create Superuser if not exists
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123', role='admin')
        print("- Created superuser: admin / admin123")
    
    # 2. Create Account Categories
    inc_cat, _ = AccountCategory.objects.get_or_name_or_create = AccountCategory.objects.get_or_create(name='General Donation', type='income')
    exp_cat, _ = AccountCategory.objects.get_or_create(name='Staff Salary', type='expense')
    AccountCategory.objects.get_or_create(name='Maintenance', type='expense')
    AccountCategory.objects.get_or_create(name='Electricity', type='expense')
    print("- Created account categories")
    
    # 3. Create Fee Structures
    FeeStructure.objects.get_or_create(name='Monthly Subscription (Member)', home_type='member', amount=Decimal('500.00'))
    FeeStructure.objects.get_or_create(name='Madrasa Fee (Non-Member)', home_type='non_member', amount=Decimal('300.00'))
    print("- Created fee structures")
    
    # 4. Create Homes and Students
    h1, _ = Home.objects.get_or_create(name='Abdullah Family', house_name='Baitul Aman', home_type='member', contact_number='9876543210')
    h2, _ = Home.objects.get_or_create(name='Yusuf Family', house_name='Green Villa', home_type='member', contact_number='9876543211', fee_exception=True)
    h3, _ = Home.objects.get_or_create(name='Zaid Family', house_name='Rose Garden', home_type='non_member', contact_number='9876543212')
    
    Student.objects.get_or_create(home=h3, name='Omar Zaid', grade='Class 2')
    Student.objects.get_or_create(home=h3, name='Aisha Zaid', grade='Class 4')
    print("- Created homes and students")
    
    # 5. Create a Special Program
    sp, _ = SpecialProgram.objects.get_or_create(name='Meelad-un-Nabi 2026', date=date(2026, 9, 15), target_budget=Decimal('50000.00'))
    print("- Created special program")
    
    # 6. Generate Invoices using the management command logic
    from django.core.management import call_command
    call_command('generate_invoices')
    print("- Generated invoices")
    
    # 7. Add some sample transactions
    Transaction.objects.create(
        transaction_type='income',
        category=inc_cat,
        amount=Decimal('10000.00'),
        date=date.today(),
        received_from_or_paid_to='Local Well-wisher',
        remarks='Initial donation'
    )
    
    Transaction.objects.create(
        transaction_type='expense',
        category=exp_cat,
        amount=Decimal('5000.00'),
        date=date.today(),
        received_from_or_paid_to='Staff Members',
        remarks='April Salary'
    )
    
    # Special program donation
    Transaction.objects.create(
        transaction_type='income',
        program=sp,
        amount=Decimal('5000.00'),
        date=date.today(),
        received_from_or_paid_to='Sponsor A',
        remarks='Meelad contribution'
    )
    
    print("Population complete!")

if __name__ == '__main__':
    populate()
