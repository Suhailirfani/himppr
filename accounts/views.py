from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import CustomUser
from .forms import UserForm

def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = CustomUser.objects.all()
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def user_create(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts:user_list')
    else:
        form = UserForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Create User'})

@login_required
@user_passes_test(is_admin)
def user_update(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('accounts:user_list')
    else:
        form = UserForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Update User', 'edit': True})

@login_required
@user_passes_test(is_admin)
def user_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        user.delete()
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'user_obj': user})
