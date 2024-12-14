from django.urls import path

from cups.views import cup_fixtures, all_cups

app_name = 'cups'

urlpatterns = [
    path('cup_fixtures.html', cup_fixtures, name='cup_fixtures'),
    path('all_cups.html', all_cups, name='all_cups')
]
