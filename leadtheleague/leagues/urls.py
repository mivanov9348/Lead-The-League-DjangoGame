from django.urls import path
from .views import standings

app_name = 'leagues'

urlpatterns = [
    path('standings/', standings, name='standings'),
    path('standings/<int:league_id>/', standings, name='standings'),
]
