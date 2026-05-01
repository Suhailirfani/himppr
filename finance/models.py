from django.db import models
from django.utils import timezone
from homes.models import Home, Student
import uuid

class AccountCategory(models.Model):
    CATEGORY_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Account Categories"
        ordering = ['type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class SpecialProgram(models.Model):
    name = models.CharField(max_length=150, help_text="e.g., Meelad 2026")
    date = models.DateField(null=True, blank=True)
    target_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    # Track the balance manually or calculate it
    # If balance > 0 (surplus), it goes to main fund at the end.
    # If balance < 0 (shortage), taken from main fund.

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.name

    @property
    def total_income(self):
        from decimal import Decimal
        return sum((tx.amount for tx in self.transactions.filter(transaction_type='income')), Decimal('0.00'))

    @property
    def total_expense(self):
        from decimal import Decimal
        return sum((tx.amount for tx in self.transactions.filter(transaction_type='expense')), Decimal('0.00'))

    @property
    def balance(self):
        return self.total_income - self.total_expense


class FeeStructure(models.Model):
    name = models.CharField(max_length=100)
    home_type = models.CharField(max_length=20, choices=Home.HOME_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_home_type_display()}) - ₹{self.amount}"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('due', 'Due'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    ]
    
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name='invoices')
    title = models.CharField(max_length=100, help_text="e.g., Subscription Fee - May 2026")
    month = models.DateField(help_text="The month this fee belongs to")
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='due')
    
    is_concession = models.BooleanField(default=False, help_text="True if fee was waived due to exception")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month', 'home']

    def __str__(self):
        return f"{self.home.name} - {self.title} ({self.status})"
    
    @property
    def balance(self):
        if self.is_concession:
            return 0
        return max(0, self.total_amount - self.amount_paid)

    def update_status(self):
        if self.is_concession:
            self.status = 'paid'
            self.amount_paid = 0
        elif self.amount_paid >= self.total_amount:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        else:
            self.status = 'due'
        self.save()


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('upi', 'UPI'),
    ]

    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    
    # Linked to general ledger OR Special Program
    category = models.ForeignKey(AccountCategory, on_delete=models.SET_NULL, null=True, blank=True)
    program = models.ForeignKey(SpecialProgram, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', help_text="Link if this belongs to a special program")
    
    # Linked to Home/Invoice
    home = models.ForeignKey('homes.Home', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    
    received_from_or_paid_to = models.CharField(max_length=200, blank=True, help_text="Name of person/org")
    recorded_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True)
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - ₹{self.amount} on {self.date}"
