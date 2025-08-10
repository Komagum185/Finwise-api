from django.urls import path
from . import views

urlpatterns = [
    path('income/', views.income_report, name='income_report'),
    path('stock/', views.stock_report, name='stock_report'),
    path('purchases/', views.purchases_report, name='purchases_report'),
    path('sales/', views.sales_report, name='sales_report'),
    path('analytics/', views.analytics_report, name='analytics_report'),
] 