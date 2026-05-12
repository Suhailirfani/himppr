from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('fee-collection/', views.fee_collection, name='fee_collection'),
    path('special-programs/', views.special_programs, name='special_programs'),
    path('reports/', views.reports, name='reports'),
    
    # Forms
    path('transaction/new/', views.transaction_create, name='transaction_create'),
    path('invoice/new/', views.invoice_create, name='invoice_create'),
    path('payment/record/', views.record_payment, name='record_payment'),
    path('program/new/', views.program_create, name='program_create'),
    path('program/<int:pk>/apply-dues/', views.apply_program_dues, name='apply_program_dues'),
    path('category/add-ajax/', views.category_create_ajax, name='category_create_ajax'),
    path('previous-balance/add/', views.add_previous_balance, name='add_previous_balance'),
    
    # Fee Structure
    path('fees/', views.fee_structure_list, name='fee_structure_list'),
    path('fees/new/', views.fee_structure_create, name='fee_structure_create'),
    path('fees/<int:pk>/update/', views.fee_structure_update, name='fee_structure_update'),
    
    # Home Individual Finance
    path('home/<int:pk>/', views.home_finance_detail, name='home_finance_detail'),
    path('home/<int:pk>/collect/', views.collect_money, name='collect_money'),
]
