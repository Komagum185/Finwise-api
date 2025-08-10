from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.dashboard_overview, name='dashboard_overview'),
    path('stats/', views.dashboard_stats, name='dashboard_stats'),
    path('charts/', views.dashboard_charts, name='dashboard_charts'),
] 