from django.urls import path
from .views import product_detail, products_list

app_name = 'shop'

urlpatterns = [
    path('', products_list, name='products_list'),
    path('<int:pk>/', product_detail, name='product_detail'),
]
