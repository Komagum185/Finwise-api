from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_home, name='reports_home'),
    path('basic/', views.basic_report, name='basic_report'),
] 