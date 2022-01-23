from django.urls import path

from .views import dashboard, result, DeleteDevice, delete_all_devices, recommendation, disease, \
    cardio_recommendation, parameters

app_name = 'cms'


urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('result/', result, name='result'),
    path('recommendation/', recommendation, name='recommendation'),
    path('delete-device/<uuid:pk>/', DeleteDevice.as_view(), name='delete_device'),
    path('delete-all-devices/', delete_all_devices, name='delete_all_devices'),
    path('disease/', disease, name='disease'),
    path('cardio_recommendation', cardio_recommendation, name='cardio_recommendation'),
    path('parameters/', parameters, name='parameters'),
]
