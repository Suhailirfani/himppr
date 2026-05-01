from django import forms
from .models import Home, Student

class HomeForm(forms.ModelForm):
    class Meta:
        model = Home
        fields = ['name', 'house_name', 'home_type', 'contact_number', 'address', 'is_active', 'fee_exception']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'house_name': forms.TextInput(attrs={'class': 'form-input'}),
            'home_type': forms.Select(attrs={'class': 'form-input'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'age', 'grade', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'age': forms.NumberInput(attrs={'class': 'form-input'}),
            'grade': forms.TextInput(attrs={'class': 'form-input'}),
        }
