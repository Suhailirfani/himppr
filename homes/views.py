from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Home, Student
from .forms import HomeForm, StudentForm
from decimal import Decimal

@login_required
def member_dashboard(request):
    # If not a home member, go to main dashboard
    if request.user.role != 'home':
        return redirect('finance:dashboard')
    
    # If home member but no profile linked, just show empty state or error instead of redirecting back
    home = request.user.home_profile
    if not home:
        return render(request, 'homes/member_dashboard.html', {'no_profile': True})
    invoices = home.invoices.all().order_by('-month')
    total_due = sum((inv.balance for inv in invoices), Decimal('0.00'))
    students = home.students.all()
    
    context = {
        'home': home,
        'invoices': invoices,
        'total_due': total_due,
        'students': students,
    }
    return render(request, 'homes/member_dashboard.html', context)

@login_required
def home_list(request):
    homes = Home.objects.all()
    return render(request, 'homes/home_list.html', {'homes': homes})

@login_required
def home_create(request):
    if request.method == 'POST':
        form = HomeForm(request.POST)
        if form.is_valid():
            home = form.save()
            if request.POST.get('create_user_account'):
                create_user_for_home(home)
            return redirect('homes:home_list')
    else:
        form = HomeForm()
    return render(request, 'homes/home_form.html', {'form': form, 'title': 'Add New Home'})

@login_required
def home_update(request, pk):
    home = get_object_or_404(Home, pk=pk)
    if request.method == 'POST':
        form = HomeForm(request.POST, instance=home)
        if form.is_valid():
            home = form.save()
            if request.POST.get('create_user_account') and not hasattr(home, 'user_account'):
                create_user_for_home(home)
            return redirect('homes:home_list')
    else:
        form = HomeForm(instance=home)
    return render(request, 'homes/home_form.html', {'form': form, 'title': 'Update Home', 'edit': True, 'home_obj': home})

def create_user_for_home(home):
    from accounts.models import CustomUser
    import re
    # Create a simple username from the home name
    username = re.sub(r'[^a-zA-Z0-9]', '', home.name).lower()
    # Ensure unique username
    base_username = username
    counter = 1
    while CustomUser.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
        
    user = CustomUser.objects.create(
        username=username,
        role='home',
        home_profile=home,
        first_name=home.name
    )
    user.set_password('madrasa123')
    user.save()
    return user

@login_required
def home_delete(request, pk):
    home = get_object_or_404(Home, pk=pk)
    if request.method == 'POST':
        home.delete()
        return redirect('homes:home_list')
    return render(request, 'homes/home_confirm_delete.html', {'home_obj': home})
