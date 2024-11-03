from django.urls import path

from leagues.views import allleagues, standings, schedule

app_name = 'leagues'

urlpatterns = [
    path('standings/', standings, name='standings'),
    path('allleagues/', allleagues, name='allleagues'),
    path('allleagues/<int:league_id>/<int:division_id>/', allleagues, name='allleagues_with_params'),
    path('schedule/', schedule, name='schedule')
]
