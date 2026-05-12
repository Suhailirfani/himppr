from django.urls import path
from . import views

app_name = 'homes'

urlpatterns = [
    path('dashboard/', views.member_dashboard, name='member_dashboard'),
    path('homes/', views.home_list, name='home_list'),
    path('homes/create/', views.home_create, name='home_create'),
    path('homes/<int:pk>/update/', views.home_update, name='home_update'),
    path('homes/<int:pk>/delete/', views.home_delete, name='home_delete'),
    path('homes/bulk-delete/', views.home_bulk_delete, name='home_bulk_delete'),
    path('homes/upload-excel/', views.home_upload_excel, name='home_upload_excel'),
    path('homes/download-template/', views.home_download_template, name='home_download_template'),
]
