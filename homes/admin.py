from django.contrib import admin
from .models import Home, Student

class StudentInline(admin.TabularInline):
    model = Student
    extra = 1

@admin.register(Home)
class HomeAdmin(admin.ModelAdmin):
    list_display = ('name', 'home_type', 'is_active', 'fee_exception')
    list_filter = ('home_type', 'is_active', 'fee_exception')
    search_fields = ('name', 'contact_number')
    inlines = [StudentInline]

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'home', 'grade', 'is_active')
    list_filter = ('is_active', 'grade')
    search_fields = ('name', 'home__name')
