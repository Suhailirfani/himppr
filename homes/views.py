from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import Home, Student
from .forms import HomeForm, StudentForm
from django.db.models import Q
from .utils import identify_and_swap
from decimal import Decimal
import openpyxl

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
    query = request.GET.get('q')
    lang = request.GET.get('lang', 'ml')
    homes = Home.objects.all()
    if query:
        homes = homes.filter(
            Q(uid__icontains=query) |
            Q(name__icontains=query) |
            Q(name_en__icontains=query) |
            Q(house_name__icontains=query) |
            Q(contact_number__icontains=query) |
            Q(area__icontains=query)
        )
    return render(request, 'homes/home_list.html', {
        'homes': homes, 
        'query': query,
        'lang': lang
    })

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
        messages.success(request, f"Home '{home.name}' deleted successfully.")
        return redirect('homes:home_list')
    return render(request, 'homes/home_confirm_delete.html', {'home_obj': home})

@login_required
def home_bulk_delete(request):
    if request.method == 'POST':
        home_ids = request.POST.getlist('home_ids')
        if home_ids:
            count = Home.objects.filter(pk__in=home_ids).delete()[0]
            messages.success(request, f"Successfully deleted {count} homes.")
        else:
            messages.warning(request, "No homes selected for deletion.")
    return redirect('homes:home_list')

@login_required
def home_upload_excel(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, "Please upload a valid Excel file.")
            return redirect('homes:home_upload_excel')
            
        try:
            wb = openpyxl.load_workbook(excel_file)
            sheet = wb.active
            
            count = 0
            # Assuming row 1 is header
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row[0]: # name is required
                    continue
                    
                raw_name = str(row[0]).strip()
                raw_name_en = str(row[1]).strip() if row[1] else ''
                
                # Automatically identify and swap if necessary
                name, name_en = identify_and_swap(raw_name, raw_name_en)
                
                house_name = str(row[2]).strip() if row[2] else ''
                home_type = str(row[3]).strip().lower() if row[3] else 'member'
                if home_type not in ['member', 'non_member']:
                    home_type = 'member'
                contact_number = str(row[4]).strip() if row[4] else ''
                address = str(row[5]).strip() if row[5] else ''
                area = str(row[6]).strip() if row[6] else ''
                fee_exception_str = str(row[7]).strip().lower() if row[7] else 'no'
                fee_exception = fee_exception_str in ['yes', 'true', '1']
                
                Home.objects.create(
                    name=name,
                    name_en=name_en,
                    house_name=house_name,
                    home_type=home_type,
                    contact_number=contact_number,
                    address=address,
                    area=area,
                    fee_exception=fee_exception
                )
                count += 1
            
            messages.success(request, f"Successfully imported {count} homes.")
            return redirect('homes:home_list')
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            return redirect('homes:home_upload_excel')

    return render(request, 'homes/home_upload_excel.html')

@login_required
def home_download_template(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Homes Template"
    
    # Headers
    headers = ["Name", "Name (English)", "House Name", "Type", "Contact", "Address", "Area", "Fee Exception"]
    ws.append(headers)
    
    # Add a sample row to guide the user
    sample_row = ["John Doe", "John Doe", "Doe Villa", "member", "1234567890", "123 Sample St", "Downtown", "No"]
    ws.append(sample_row)
    
    # Auto-adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter # Get the column name
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="homes_upload_template.xlsx"'
    wb.save(response)
    
    return response
