from django.urls import path
from . import views

urlpatterns = [
    path('', views.converter_home, name='converter-home'),
    path('api/convert/', views.convert_api, name='convert-api'),
    path('api/history/', views.history_api, name='history-api'),
]