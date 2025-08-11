from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('overview/', views.dashboard_overview, name='dashboard_overview'),
] 