from django.urls import path
from . import views

urlpatterns = [
    path('team/<int:team_id>/squad/', views.team_squad, name='team_squad'),
]
