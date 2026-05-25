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
    path('areas/', views.area_list, name='area_list'),
    path('areas/create/', views.area_create, name='area_create'),
    path('areas/<int:pk>/update/', views.area_update, name='area_update'),
    path('areas/<int:pk>/delete/', views.area_delete, name='area_delete'),
    path('areas/create-ajax/', views.area_create_ajax, name='area_create_ajax'),
]
