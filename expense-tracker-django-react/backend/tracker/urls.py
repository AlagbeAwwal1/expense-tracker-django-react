from django.urls import path
from . import views

urlpatterns = [
    path('files/', views.upload_csv),
    path('transactions/', views.transactions_list),
    path('transactions/<int:pk>/', views.transaction_detail),
    path('analytics/spend-by-category/', views.spend_by_category),
    path('seed/', views.seed_defaults),
    path('analytics/monthly-category-totals/', views.monthly_category_totals),
    path('transactions/clear/', views.delete_transaction),
    path("health/", views.health),
]
