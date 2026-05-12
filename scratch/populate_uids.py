import os
import sys
import django

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'himppr_erp.settings')
django.setup()

from homes.models import Home

def populate_uids():
    homes = Home.objects.filter(uid__isnull=True).order_by('id')
    count = Home.objects.exclude(uid__isnull=True).count()
    
    for home in homes:
        count += 1
        uid = f'H-{count:04d}'
        while Home.objects.filter(uid=uid).exists():
            count += 1
            uid = f'H-{count:04d}'
        home.uid = uid
        home.save()

if __name__ == "__main__":
    populate_uids()
