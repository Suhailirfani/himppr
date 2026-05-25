from django import forms
from .models import Home, Student, Area

class AreaForm(forms.ModelForm):
    id = forms.IntegerField(required=False, label="ID", widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Auto-increment if left blank'}))

    class Meta:
        model = Area
        fields = ['id', 'name', 'name_en']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'name_en': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Name in English'}),
        }

class HomeForm(forms.ModelForm):
    class Meta:
        model = Home
        fields = ['name', 'name_en', 'house_name', 'home_type', 'contact_number', 'area', 'address', 'is_active', 'fee_exception']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'name_en': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Name in English'}),
            'house_name': forms.TextInput(attrs={'class': 'form-input'}),
            'home_type': forms.Select(attrs={'class': 'form-input'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-input'}),
            'area': forms.Select(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['area'].empty_label = "Select Area"

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'age', 'grade', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'age': forms.NumberInput(attrs={'class': 'form-input'}),
            'grade': forms.TextInput(attrs={'class': 'form-input'}),
        }
