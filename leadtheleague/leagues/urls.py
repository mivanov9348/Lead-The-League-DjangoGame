from django.urls import path
from leagues.views import allleagues, standings, league_results

app_name = 'leagues'

urlpatterns = [
    path('standings/', standings, name='standings'),
    path('allleagues/', allleagues, name='allleagues'),
    path('league_results', league_results, name='league_results'),
]
