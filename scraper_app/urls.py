from django.urls import path
from . import views

urlpatterns = [
    path('', views.search_apps, name='search_apps'),
    path('download/', views.download_excel, name='download_excel'),
]