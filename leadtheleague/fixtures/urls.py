from fixtures.views import results
from django.urls import path

app_name = 'fixtures'

urlpatterns = [
    path('results', results, name='results'),
    path('round/<int:round_number>/', results, name='fixtures_list_with_round'),
]
