# keyword_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_file, name='upload_file'),
    path('result/', views.result_view, name='result_view'),
]
