from django.urls import path, include

# Partner only has access to the partner dashboard
urlpatterns = [
    # Partner Dashboard - legacy endpoint that partners use
    path('dashboard/', include('partner_dashboard.urls')),
]
