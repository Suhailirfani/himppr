from django import forms
from .models import Transaction, Invoice, SpecialProgram, AccountCategory

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'category', 'program', 'amount', 'date', 'payment_method', 'received_from_or_paid_to', 'remarks']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-input', 'id': 'id_transaction_type'}),
            'category': forms.Select(attrs={'class': 'form-input', 'id': 'id_category'}),
            'program': forms.Select(attrs={'class': 'form-input'}),
            'amount': forms.NumberInput(attrs={'class': 'form-input'}),
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-input'}),
            'received_from_or_paid_to': forms.TextInput(attrs={'class': 'form-input'}),
            'remarks': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'initial' in kwargs and 'transaction_type' in kwargs['initial']:
            tx_type = kwargs['initial']['transaction_type']
            self.fields['category'].queryset = AccountCategory.objects.filter(type=tx_type)
        elif self.instance.pk:
            self.fields['category'].queryset = AccountCategory.objects.filter(type=self.instance.transaction_type)

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['home', 'title', 'month', 'total_amount', 'status', 'is_concession']
        widgets = {
            'home': forms.Select(attrs={'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'month': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
        }

class SpecialProgramForm(forms.ModelForm):
    class Meta:
        model = SpecialProgram
        fields = ['name', 'date', 'target_budget', 'per_member_amount', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'target_budget': forms.NumberInput(attrs={'class': 'form-input'}),
            'per_member_amount': forms.NumberInput(attrs={'class': 'form-input'}),
        }

class PreviousBalanceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['home', 'title', 'total_amount', 'month']
        labels = {
            'title': 'Particular',
            'month': 'Date',
            'total_amount': 'Balance Amount'
        }
        widgets = {
            'home': forms.Select(attrs={'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Subscription Fee, Special Fund'}),
            'month': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-input'}),
        }

class PaymentRecordForm(forms.Form):
    invoice = forms.ModelChoiceField(queryset=Invoice.objects.exclude(status='paid'), widget=forms.Select(attrs={'class': 'form-input'}))
    amount = forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-input'}))
    date = forms.DateField(initial=forms.DateInput().format_value(forms.DateField().initial), widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}))
    payment_method = forms.ChoiceField(choices=Transaction.PAYMENT_METHODS, widget=forms.Select(attrs={'class': 'form-input'}))
    remarks = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 2}))
