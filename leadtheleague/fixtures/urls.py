from fixtures.views import fixtures
from django.urls import path

app_name = 'fixtures'

urlpatterns = [
    path('fixtures', fixtures, name='fixtures'),
    path('round/<int:round_number>/', fixtures, name='fixtures_list_with_round'),

]
