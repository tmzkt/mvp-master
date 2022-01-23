from django.urls import path, re_path, reverse_lazy
from publication import views


app_name = 'publication'

urlpatterns = [
    path('', views.publication, name='publication'),
]
