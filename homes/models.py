from django.db import models

class Area(models.Model):
    name = models.CharField(max_length=150, unique=True, help_text="Name of the area/locality")
    name_en = models.CharField(max_length=150, blank=True, help_text="Name in English")

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name

class Home(models.Model):
    HOME_TYPE_CHOICES = [
        ('member', 'Member Home'),
        ('non_member', 'Non-Member Home'),
    ]
    name = models.CharField(max_length=150, help_text="Family Name or Head of Household")
    name_en = models.CharField(max_length=150, blank=True, help_text="Name in English")
    house_name = models.CharField(max_length=150, blank=True)
    home_type = models.CharField(max_length=20, choices=HOME_TYPE_CHOICES, default='member')
    contact_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='homes', verbose_name="Area/Locality")
    
    is_active = models.BooleanField(default=True)
    fee_exception = models.BooleanField(default=False, help_text="Check if this home is exempted from paying fees (e.g., poor family)")
    advance_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Money paid in advance by this home")

    uid = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Home ID")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.uid:
            # Generate a unique ID if not present
            # We use the count + 1 to get a sequential ID
            # Note: For high concurrency, this might need a more robust approach,
            # but for this ERP it should be fine.
            count = Home.objects.count()
            self.uid = f'H-{(count + 1):04d}'
            # Ensure uniqueness in case of deletions
            while Home.objects.filter(uid=self.uid).exists():
                count += 1
                self.uid = f'H-{(count + 1):04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.uid} - {self.name} ({self.get_home_type_display()})"


class Student(models.Model):
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name='students')
    name = models.CharField(max_length=150)
    age = models.PositiveIntegerField(null=True, blank=True)
    grade = models.CharField(max_length=50, blank=True, help_text="Class/Grade in Madrasa")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (Child of {self.home.name})"
