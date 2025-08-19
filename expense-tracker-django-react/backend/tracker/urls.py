from django.urls import path
from . import views

urlpatterns = [
    path('files/', views.upload_csv),
    path('transactions/', views.transactions_list),
    path('transactions/<int:pk>/', views.transaction_detail),
    path('analytics/spend-by-category/', views.spend_by_category),
    path('seed/', views.seed_defaults),
]
