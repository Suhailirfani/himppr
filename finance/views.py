from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Invoice, Transaction, SpecialProgram, AccountCategory
from homes.models import Home
from django.db.models import Sum
from .forms import TransactionForm, InvoiceForm, SpecialProgramForm, PaymentRecordForm, PreviousBalanceForm
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.utils import timezone

@login_required
def dashboard(request):
    # Auto-generate invoices for the month if not already done
    from .utils import auto_generate_monthly_invoices
    auto_generate_monthly_invoices()

    # Redirect Home Members to their specific dashboard
    if request.user.role == 'home':
        return redirect('homes:member_dashboard')

    # Total Finance Dashboard
    total_income = Transaction.objects.filter(transaction_type='income', program__isnull=True).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_expense = Transaction.objects.filter(transaction_type='expense', program__isnull=True).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    main_balance = total_income - total_expense
    
    recent_transactions = Transaction.objects.all().order_by('-date', '-created_at')[:5]

    lang = request.GET.get('lang', 'en') # Finance defaults to English as per previous request, but we'll allow toggle
    
    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'main_balance': main_balance,
        'recent_transactions': recent_transactions,
        'lang': lang,
    }
    return render(request, 'finance/dashboard.html', context)


@login_required
def fee_collection(request):
    # Search functionality
    query = request.GET.get('q', '')
    homes = Home.objects.filter(is_active=True)
    if query:
        from django.db.models import Q
        homes = homes.filter(
            Q(uid__icontains=query) |
            Q(name__icontains=query) |
            Q(name_en__icontains=query) |
            Q(house_name__icontains=query) |
            Q(area__name__icontains=query) |
            Q(area__name_en__icontains=query) |
            Q(contact_number__icontains=query)
        )
    
    invoices = Invoice.objects.all().order_by('-month')
    total_due = sum((inv.balance for inv in invoices), Decimal('0.00'))
    
    lang = request.GET.get('lang', 'en')
    
    context = {
        'homes': homes,
        'query': query,
        'total_due': total_due,
        'latest_invoices': invoices[:10],
        'lang': lang,
    }
    return render(request, 'finance/fee_collection.html', context)


@login_required
def home_finance_detail(request, pk):
    home = get_object_or_404(Home, pk=pk)
    invoices = home.invoices.all().order_by('-month')
    total_balance = sum((inv.balance for inv in invoices), Decimal('0.00'))
    
    transactions = home.transactions.all().order_by('-date', '-created_at')[:15]
    
    lang = request.GET.get('lang', 'en')
    
    context = {
        'home': home,
        'invoices': invoices,
        'total_balance': total_balance,
        'transactions': transactions,
        'lang': lang,
    }
    return render(request, 'finance/home_detail.html', context)


@login_required
def collect_money(request, pk):
    home = get_object_or_404(Home, pk=pk)
    
    # Calculate upcoming months (next 6 months)
    from dateutil.relativedelta import relativedelta
    from datetime import date
    today = timezone.now().date()
    current_month = date(today.year, today.month, 1)
    upcoming_months = []
    for i in range(1, 7):
        m = current_month + relativedelta(months=i)
        upcoming_months.append({
            'date': m.isoformat(),
            'label': m.strftime("%B %Y"),
            'exists': home.invoices.filter(month=m, invoice_type='subscription').exists()
        })

    due_invoices = list(home.invoices.exclude(status='paid').order_by('month'))
    total_due = sum((inv.balance for inv in due_invoices), Decimal('0.00'))
    
    if request.method == 'POST':
        selected_future_months = request.POST.getlist('future_months')
        payment_method = request.POST.get('payment_method', 'cash')
        
        amount_raw = request.POST.get('amount', '0')
        if not amount_raw: amount_raw = '0'
        amount = Decimal(amount_raw).quantize(Decimal('0.00'))
        
        # 1. Create future invoices if selected
        from .models import FeeStructure
        for m_str in selected_future_months:
            m_date = date.fromisoformat(m_str)
            if not home.invoices.filter(month=m_date, invoice_type='subscription').exists():
                amount_to_charge = 0
                title = f"Subscription Fee - {m_date.strftime('%B %Y')}"
                if home.home_type == 'member':
                    fee_struct = FeeStructure.objects.filter(home_type='member', is_active=True).first()
                    if fee_struct: amount_to_charge = fee_struct.amount
                elif home.home_type == 'non_member':
                    active_students = home.students.filter(is_active=True).count()
                    fee_struct = FeeStructure.objects.filter(home_type='non_member', is_active=True).first()
                    if fee_struct: amount_to_charge = fee_struct.amount * active_students
                
                if amount_to_charge > 0:
                    inv = Invoice.objects.create(
                        home=home, title=title, invoice_type='subscription',
                        month=m_date, total_amount=amount_to_charge,
                        amount_paid=0, status='due', is_concession=home.fee_exception
                    )
                    due_invoices.append(inv)

        # Re-sort due invoices by month
        due_invoices.sort(key=lambda x: x.month)
        
        date_received = request.POST.get('date', timezone.now().date())
        remarks = request.POST.get('remarks', '')
        sub_fee_cat, _ = AccountCategory.objects.get_or_create(name='Subscription Fee', type='income')

        # 2. Determine funds to apply
        remaining_funds = amount
        if payment_method == 'wallet':
            # Cap by actual wallet balance
            remaining_funds = min(amount, home.advance_balance)
            
        initial_funds = remaining_funds

        # 3. Apply funds to invoices
        for inv in due_invoices:
            if remaining_funds <= 0: break
            
            balance = inv.balance
            if balance <= 0: continue
            
            payment_to_apply = min(remaining_funds, balance)
            
            # Record Transaction
            Transaction.objects.create(
                transaction_type='income', category=sub_fee_cat, home=home, invoice=inv,
                amount=payment_to_apply, date=date_received, payment_method=payment_method,
                received_from_or_paid_to=home.name, recorded_by=request.user, 
                remarks=f"Payment for {inv.title}. {remarks}"
            )
            
            inv.amount_paid += payment_to_apply
            inv.update_status()
            remaining_funds -= payment_to_apply

        # 4. Update Wallet Balance
        if payment_method == 'wallet':
            # Reduce wallet by the amount actually used
            amount_used = initial_funds - remaining_funds
            home.advance_balance -= amount_used
        else:
            # New money payment, leftovers go to wallet
            if remaining_funds > 0:
                home.advance_balance += remaining_funds
                
                Transaction.objects.create(
                    transaction_type='income', category=sub_fee_cat, home=home,
                    amount=remaining_funds, date=date_received, payment_method=payment_method,
                    received_from_or_paid_to=home.name, recorded_by=request.user,
                    remarks=f"Wallet Top-up from excess payment. {remarks}"
                )
        
        home.save()
        return redirect('finance:home_finance_detail', pk=pk)

    context = {
        'home': home,
        'total_due': total_due,
        'due_invoices': due_invoices,
        'upcoming_months': upcoming_months,
        'today': timezone.now().date(),
        'lang': request.GET.get('lang', 'en'),
    }
    return render(request, 'finance/collect_money.html', context)


@login_required
def special_programs(request):
    programs = SpecialProgram.objects.all()
    context = {
        'programs': programs,
    }
    return render(request, 'finance/special_programs.html', context)


@login_required
def reports(request):
    # Filtering logic
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    category_id = request.GET.get('category')
    tx_type = request.GET.get('type')
    active_tab = request.GET.get('tab', 'summary')

    transactions = Transaction.objects.all()

    if start_date:
        transactions = transactions.filter(date__gte=start_date)
    if end_date:
        transactions = transactions.filter(date__lte=end_date)
    if category_id:
        if category_id == 'None':
            transactions = transactions.filter(category__isnull=True)
        else:
            transactions = transactions.filter(category_id=category_id)
    if tx_type:
        transactions = transactions.filter(transaction_type=tx_type)

    total_income = transactions.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    total_expense = transactions.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    # Calculate initial balance before the start_date if filtering is active
    initial_balance = Decimal('0.00')
    if start_date:
        pre_income = Transaction.objects.filter(date__lt=start_date, transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        pre_expense = Transaction.objects.filter(date__lt=start_date, transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        initial_balance = pre_income - pre_expense
    else:
        # If no start date, we still need to handle the earliest transactions
        first_tx = Transaction.objects.all().order_by('date').first()
        if first_tx:
            # We'll calculate month by month from the very beginning to get accurate carry-overs
            pass

    # 1. Item-wise Summary (By Category)
    category_summary = transactions.values('category__id', 'category__name', 'transaction_type').annotate(total=Sum('amount')).order_by('transaction_type', 'category__name')
    
    # 2. Daily Summary with Items and Carry-over
    from django.db.models.functions import TruncDay
    daily_items = transactions.annotate(day_trunc=TruncDay('date')).values('day_trunc', 'category__name', 'transaction_type').annotate(total=Sum('amount')).order_by('day_trunc', 'transaction_type', 'category__name')
    
    # Group items by day first
    temp_daily = {}
    for item in daily_items:
        day = item['day_trunc']
        if day not in temp_daily:
            temp_daily[day] = {'income_total': 0, 'expense_total': 0, 'income_items': [], 'expense_items': []}
        
        val = item['total']
        cat_name = item['category__name'] or "Uncategorized"
        if item['transaction_type'] == 'income':
            temp_daily[day]['income_total'] += val
            temp_daily[day]['income_items'].append({'name': cat_name, 'total': val})
        else:
            temp_daily[day]['expense_total'] += val
            temp_daily[day]['expense_items'].append({'name': cat_name, 'total': val})

    # Calculate Daily Carry-over
    current_daily_balance = initial_balance
    daily_data = {}
    sorted_days = sorted(temp_daily.keys())
    for day in sorted_days:
        data = temp_daily[day]
        data['opening_balance'] = current_daily_balance
        data['net_balance'] = data['income_total'] - data['expense_total']
        data['closing_balance'] = data['opening_balance'] + data['net_balance']
        current_daily_balance = data['closing_balance']
        daily_data[day] = data
    
    # Reverse for display
    daily_data = dict(reversed(list(daily_data.items())))
    
    # 3. Monthly Summary with Items and Carry-over Balance
    from django.db.models.functions import TruncMonth
    
    monthly_items = transactions.annotate(month_trunc=TruncMonth('date')).values('month_trunc', 'category__name', 'transaction_type').annotate(total=Sum('amount')).order_by('month_trunc', 'transaction_type', 'category__name')
    
    # Group items by month first (Chronological order for balance calculation)
    temp_data = {}
    for item in monthly_items:
        month = item['month_trunc']
        if month not in temp_data:
            temp_data[month] = {'income_total': 0, 'expense_total': 0, 'income_items': [], 'expense_items': []}
        
        val = item['total']
        cat_name = item['category__name'] or "Uncategorized"
        if item['transaction_type'] == 'income':
            temp_data[month]['income_total'] += val
            temp_data[month]['income_items'].append({'name': cat_name, 'total': val})
        else:
            temp_data[month]['expense_total'] += val
            temp_data[month]['expense_items'].append({'name': cat_name, 'total': val})

    # Calculate Carry-over (Opening/Closing) Balances
    current_running_balance = initial_balance
    monthly_data = {}
    sorted_months = sorted(temp_data.keys())
    
    for month in sorted_months:
        data = temp_data[month]
        data['opening_balance'] = current_running_balance
        data['net_balance'] = data['income_total'] - data['expense_total']
        data['closing_balance'] = data['opening_balance'] + data['net_balance']
        current_running_balance = data['closing_balance']
        monthly_data[month] = data

    # Reverse for display (Newest first)
    monthly_data = dict(reversed(list(monthly_data.items())))

    categories = AccountCategory.objects.all()

    context = {
        'transactions': transactions,
        'categories': categories,
        'category_summary': category_summary,
        'daily_data': daily_data,
        'monthly_data': monthly_data,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_total': total_income - total_expense,
        'active_tab': active_tab,
        'lang': lang,
    }
    return render(request, 'finance/reports.html', context)


@login_required
def transaction_create(request):
    tx_type = request.GET.get('type', 'income')
    program_id = request.GET.get('program')
    
    initial = {'transaction_type': tx_type}
    if program_id:
        initial['program'] = program_id
        
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.recorded_by = request.user
            tx.save()
            if tx.program:
                return redirect('finance:special_programs')
            return redirect('finance:dashboard')
    else:
        form = TransactionForm(initial=initial)
    
    title = f"New {tx_type.capitalize()}"
    if program_id:
        title += " for Program"
        
    return render(request, 'finance/form.html', {'form': form, 'title': title})


@login_required
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('finance:fee_collection')
    else:
        form = InvoiceForm()
    return render(request, 'finance/form.html', {'form': form, 'title': 'Generate Manual Invoice'})


@login_required
def record_payment(request):
    invoice_id = request.GET.get('invoice')
    initial = {}
    if invoice_id:
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        initial = {'invoice': invoice, 'amount': invoice.balance}
        
    if request.method == 'POST':
        form = PaymentRecordForm(request.POST)
        if form.is_valid():
            invoice = form.cleaned_data['invoice']
            amount = form.cleaned_data['amount']
            
            # Get or create Subscription Fee category
            sub_fee_cat, _ = AccountCategory.objects.get_or_create(name='Subscription Fee', type='income')
            
            # Create Transaction
            Transaction.objects.create(
                transaction_type='income',
                category=sub_fee_cat,
                invoice=invoice,
                home=invoice.home,
                amount=amount,
                date=form.cleaned_data['date'],
                payment_method=form.cleaned_data['payment_method'],
                received_from_or_paid_to=invoice.home.name,
                recorded_by=request.user,
                remarks=form.cleaned_data['remarks']
            )
            
            # Update Invoice
            invoice.amount_paid += amount
            invoice.update_status()
            
            return redirect('finance:fee_collection')
    else:
        form = PaymentRecordForm(initial=initial)
    return render(request, 'finance/form.html', {'form': form, 'title': 'Record Fee Payment'})

@login_required
def category_create_ajax(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        tx_type = request.POST.get('type')
        if name and tx_type:
            category, created = AccountCategory.objects.get_or_create(name=name, type=tx_type)
            return JsonResponse({
                'id': category.id,
                'name': f"{category.name} ({category.get_type_display()})",
                'type': category.type
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def program_create(request):
    if request.method == 'POST':
        form = SpecialProgramForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('finance:special_programs')
    else:
        form = SpecialProgramForm()
    return render(request, 'finance/form.html', {'form': form, 'title': 'New Special Program'})

@login_required
def fee_structure_list(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('finance:dashboard')
    from .models import FeeStructure
    structures = FeeStructure.objects.all()
    return render(request, 'finance/fee_structure_list.html', {'structures': structures})

@login_required
def fee_structure_create(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('finance:dashboard')
    from .models import FeeStructure
    if request.method == 'POST':
        name = request.POST.get('name')
        home_type = request.POST.get('home_type')
        amount = request.POST.get('amount')
        if name and home_type and amount:
            FeeStructure.objects.create(name=name, home_type=home_type, amount=amount)
            return redirect('finance:fee_structure_list')
    return render(request, 'finance/fee_structure_form.html', {'title': 'Add Fee Structure'})

@login_required
def fee_structure_update(request, pk):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('finance:dashboard')
    from .models import FeeStructure
    structure = get_object_or_404(FeeStructure, pk=pk)
    if request.method == 'POST':
        structure.name = request.POST.get('name')
        structure.home_type = request.POST.get('home_type')
        structure.amount = request.POST.get('amount')
        structure.save()
        return redirect('finance:fee_structure_list')
    return render(request, 'finance/fee_structure_form.html', {'structure': structure, 'title': 'Update Fee Structure'})

@login_required
def apply_program_dues(request, pk):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('finance:special_programs')
    
    program = get_object_or_404(SpecialProgram, pk=pk)
    if program.per_member_amount <= 0:
        # Cannot apply zero amount
        return redirect('finance:special_programs')
        
    active_homes = Home.objects.filter(is_active=True, home_type='member')
    invoices_created = 0
    
    for home in active_homes:
        # Check if already applied to this home for this program
        if Invoice.objects.filter(home=home, program=program).exists():
            continue
            
        Invoice.objects.create(
            home=home,
            title=f"{program.name} - Fund Collection",
            invoice_type='special_program',
            program=program,
            month=program.date or timezone.now().date(),
            total_amount=program.per_member_amount,
            amount_paid=0,
            status='paid' if home.fee_exception else 'due',
            is_concession=home.fee_exception
        )
        invoices_created += 1

    if invoices_created > 0:
        messages.success(request, f"Successfully generated {invoices_created} dues for '{program.name}'.")
    else:
        messages.info(request, f"Dues for '{program.name}' were already applied or no active members found.")
        
    return redirect('finance:special_programs')

@login_required
def add_previous_balance(request):
    home_id = request.GET.get('home')
    initial = {'invoice_type': 'previous_balance'}
    if home_id:
        initial['home'] = home_id
        
    if request.method == 'POST':
        form = PreviousBalanceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.invoice_type = 'previous_balance'
            invoice.save()
            if home_id:
                return redirect('finance:home_finance_detail', pk=home_id)
            return redirect('finance:fee_collection')
    else:
        form = PreviousBalanceForm(initial=initial)
        
    return render(request, 'finance/form.html', {'form': form, 'title': 'Add Previous Balance'})
