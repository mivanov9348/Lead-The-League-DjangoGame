from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    path('mainmenu/', views.mainmenu, name='mainmenu'),
    path('home/', views.home, name='home')
]