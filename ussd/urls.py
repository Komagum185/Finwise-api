from django.urls import path
from .views import USSDAPIView

urlpatterns = [
    path('', USSDAPIView.as_view(), name='ussd-entry'),
]


