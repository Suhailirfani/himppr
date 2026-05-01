from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from finance.models import Invoice, FeeStructure
from homes.models import Home, Student

class Command(BaseCommand):
    help = 'Generate monthly invoices for all active homes'

    def handle(self, *args, **kwargs):
        current_date = timezone.now().date()
        # Use the first of the current month
        month_date = date(current_date.year, current_date.month, 1)
        month_str = month_date.strftime("%B %Y")
        
        active_homes = Home.objects.filter(is_active=True)
        
        invoices_created = 0
        
        for home in active_homes:
            # Check if invoice already exists for this month
            if Invoice.objects.filter(home=home, month=month_date).exists():
                continue
                
            amount_to_charge = 0
            title = ""
            
            if home.home_type == 'member':
                # Member gets standard monthly subscription
                fee_struct = FeeStructure.objects.filter(home_type='member', is_active=True).first()
                if fee_struct:
                    amount_to_charge = fee_struct.amount
                    title = f"Subscription Fee - {month_str}"
            elif home.home_type == 'non_member':
                # Non-member pays per active student
                active_students = home.students.filter(is_active=True).count()
                if active_students > 0:
                    fee_struct = FeeStructure.objects.filter(home_type='non_member', is_active=True).first()
                    if fee_struct:
                        amount_to_charge = fee_struct.amount * active_students
                        title = f"Madrasa Fee ({active_students} Students) - {month_str}"
                        
            # If there's an amount to charge, create invoice
            if amount_to_charge > 0:
                is_concession = home.fee_exception
                
                Invoice.objects.create(
                    home=home,
                    title=title,
                    month=month_date,
                    total_amount=amount_to_charge,
                    amount_paid=0,
                    status='paid' if is_concession else 'due',
                    is_concession=is_concession
                )
                invoices_created += 1
                
        self.stdout.write(self.style.SUCCESS(f'Successfully generated {invoices_created} invoices for {month_str}'))
