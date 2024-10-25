from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    path('home/', views.home, name='home')
]