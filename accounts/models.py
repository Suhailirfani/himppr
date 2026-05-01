from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Committee (Admin)'),
        ('staff', 'Staff'),
        ('home', 'Home Member'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    home_profile = models.OneToOneField('homes.Home', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_account')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps

@receiver(post_save, sender=CustomUser)
def create_home_profile(sender, instance, created, **kwargs):
    if created and instance.role == 'home' and not instance.home_profile:
        Home = apps.get_model('homes', 'Home')
        # Create a placeholder home record
        home = Home.objects.create(
            name=instance.get_full_name() or instance.username,
            house_name="Auto Created",
            home_type='non_member' # Default to non-member, can be edited
        )
        instance.home_profile = home
        instance.save()
