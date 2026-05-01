from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Invoice, Transaction, SpecialProgram, AccountCategory
from homes.models import Home
from django.db.models import Sum
from .forms import TransactionForm, InvoiceForm, SpecialProgramForm, PaymentRecordForm
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

    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'main_balance': main_balance,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'finance/dashboard.html', context)


@login_required
def fee_collection(request):
    # Search functionality
    query = request.GET.get('q', '')
    homes = Home.objects.filter(is_active=True)
    if query:
        homes = homes.filter(name__icontains=query) | homes.filter(house_name__icontains=query)
    
    invoices = Invoice.objects.all().order_by('-month')
    total_due = sum((inv.balance for inv in invoices), Decimal('0.00'))
    
    context = {
        'homes': homes,
        'query': query,
        'total_due': total_due,
        'latest_invoices': invoices[:10],
    }
    return render(request, 'finance/fee_collection.html', context)


@login_required
def home_finance_detail(request, pk):
    home = get_object_or_404(Home, pk=pk)
    invoices = home.invoices.all().order_by('-month')
    total_balance = sum((inv.balance for inv in invoices), Decimal('0.00'))
    
    transactions = home.transactions.all().order_by('-date', '-created_at')[:15]
    
    context = {
        'home': home,
        'invoices': invoices,
        'total_balance': total_balance,
        'transactions': transactions,
    }
    return render(request, 'finance/home_detail.html', context)


@login_required
def collect_money(request, pk):
    home = get_object_or_404(Home, pk=pk)
    due_invoices = home.invoices.exclude(status='paid').order_by('month')
    total_due = sum((inv.balance for inv in due_invoices), Decimal('0.00'))
    
    if request.method == 'POST':
        amount_raw = request.POST.get('amount', '0')
        if not amount_raw: amount_raw = '0'
        amount = Decimal(amount_raw).quantize(Decimal('0.00'))
        
        payment_method = request.POST.get('payment_method', 'cash')
        date_received = request.POST.get('date', timezone.now().date())
        remarks = request.POST.get('remarks', '')
        
        remaining_payment = amount
        
        # Get or create Subscription Fee category
        sub_fee_cat, _ = AccountCategory.objects.get_or_create(name='Subscription Fee', type='income')
        
        # Apply to invoices sequentially (oldest first)
        for inv in due_invoices:
            if remaining_payment <= 0:
                break
            
            balance = inv.balance
            payment_to_apply = min(remaining_payment, balance)
            
            # Create Transaction
            Transaction.objects.create(
                transaction_type='income',
                category=sub_fee_cat,
                home=home,
                invoice=inv,
                amount=payment_to_apply,
                date=date_received,
                payment_method=payment_method,
                received_from_or_paid_to=home.name,
                recorded_by=request.user,
                remarks=f"Payment for {inv.title}. {remarks}"
            )
            
            inv.amount_paid += payment_to_apply
            inv.update_status()
            remaining_payment -= payment_to_apply
            
        # Record advance if any left
        if remaining_payment > 0:
            home.advance_balance += remaining_payment
            home.save()
            
            # Record advance transaction (without linked invoice)
            Transaction.objects.create(
                transaction_type='income',
                category=sub_fee_cat,
                home=home,
                amount=remaining_payment,
                date=date_received,
                payment_method=payment_method,
                received_from_or_paid_to=home.name,
                recorded_by=request.user,
                remarks=f"Advance Payment received. {remarks}"
            )
            
        return redirect('finance:home_finance_detail', pk=pk)
        
    context = {
        'home': home,
        'total_due': total_due,
        'due_invoices': due_invoices,
        'today': timezone.now().date(),
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
    
    # Category-wise summary
    category_summary = transactions.values('category__id', 'category__name', 'transaction_type').annotate(total=Sum('amount')).order_by('transaction_type')
    
    categories = AccountCategory.objects.all()

    context = {
        'transactions': transactions,
        'categories': categories,
        'category_summary': category_summary,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_total': total_income - total_expense,
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
