from django.contrib import admin
from .models import AccountCategory, SpecialProgram, FeeStructure, Invoice, Transaction

@admin.register(AccountCategory)
class AccountCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')
    list_filter = ('type',)

@admin.register(SpecialProgram)
class SpecialProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'target_budget', 'is_active')

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'home_type', 'amount', 'is_active')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('home', 'title', 'month', 'total_amount', 'status', 'is_concession')
    list_filter = ('status', 'month', 'is_concession')
    search_fields = ('home__name', 'title')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'amount', 'date', 'payment_method', 'category', 'program')
    list_filter = ('transaction_type', 'payment_method', 'date')
    search_fields = ('received_from_or_paid_to', 'remarks')
