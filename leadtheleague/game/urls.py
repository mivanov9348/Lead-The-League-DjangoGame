from django.urls import path
from .views import mainmenu


urlpatterns = [
    path('mainmenu/', mainmenu, name='mainmenu')
]