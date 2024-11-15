from django.urls import path
from . import views
from .views import playerscards

app_name = 'players'

urlpatterns = [
    path('all_players/', views.all_players, name='all_players'),
    path('playerscards/', playerscards, name='playerscards')
]
