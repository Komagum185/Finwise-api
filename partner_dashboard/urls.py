from django.urls import path
from . import views

app_name = 'partner_dashboard'

urlpatterns = [
    # Dashboard summaries and graphs
    path('summaries/', views.dashboard_summaries, name='dashboard_summaries'),
    path('graphs/', views.dashboard_graphs, name='dashboard_graphs'),
    
    # Reports
    path('reports/', views.report_list, name='report_list'),
    
    # Export functionality (must come BEFORE specific report URLs to avoid conflicts)
    path('reports/digitization/export/', views.export_report, kwargs={'report_type': 'digitization'}, name='export_digitization'),
    path('reports/loans/export/', views.export_report, kwargs={'report_type': 'loans'}, name='export_loans'),
    path('reports/digital-services/export/', views.export_report, kwargs={'report_type': 'digital_services'}, name='export_digital_services'),
    
    # Alternative export URLs with format parameter
    path('reports/digitization/export/csv/', views.export_report, kwargs={'report_type': 'digitization', 'format': 'csv'}, name='export_digitization_csv'),
    path('reports/digitization/export/pdf/', views.export_report, kwargs={'report_type': 'digitization', 'format': 'pdf'}, name='export_digitization_pdf'),
    path('reports/loans/export/csv/', views.export_report, kwargs={'report_type': 'loans', 'format': 'csv'}, name='export_loans_csv'),
    path('reports/loans/export/pdf/', views.export_report, kwargs={'report_type': 'loans', 'format': 'pdf'}, name='export_loans_pdf'),
    path('reports/digital-services/export/csv/', views.export_report, kwargs={'report_type': 'digital_services', 'format': 'csv'}, name='export_digital_services_csv'),
    path('reports/digital-services/export/pdf/', views.export_report, kwargs={'report_type': 'digital_services', 'format': 'pdf'}, name='export_digital_services_pdf'),
    
    # Specific report URLs
    path('reports/digitization/', views.digitization_report, name='digitization_report'),
    path('reports/loans/', views.loan_report, name='loan_report'),
    path('reports/digital-services/', views.digital_service_report, name='digital_service_report'),
    path('access-log/', views.dashboard_access_log, name='dashboard_access_log'),
    path('filter-options/', views.filter_options, name='filter_options'),
]
