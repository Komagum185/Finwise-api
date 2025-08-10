from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'budgets', views.BudgetViewSet, basename='budget')
router.register(r'goals', views.GoalViewSet, basename='goal')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'profiles', views.UserProfileViewSet, basename='profile')
router.register(r'recurring-transactions', views.RecurringTransactionViewSet, basename='recurring-transaction')

urlpatterns = [
    path('', include(router.urls)),
] 