from django.urls import path
from europeancups.views import european_cup_groups, european_cup_knockouts

app_name = 'europeancups'

urlpatterns = [
    path('groups/', european_cup_groups, name='european_cup_groups'),
    path('knockouts/', european_cup_knockouts, name='european_cup_knockouts'),
]
