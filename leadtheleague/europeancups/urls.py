from django.urls import path

from europeancups.views import european_cup

app_name = 'europeancups'

urlpatterns = [
    path('european_cup', european_cup, name='european_cup')
]
