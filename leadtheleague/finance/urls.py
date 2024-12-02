from django.urls import path
from finance.views import team_finance

app_name = 'finance'

urlpatterns = [
    path('team_finance/', team_finance, name='team_finance'),
]
