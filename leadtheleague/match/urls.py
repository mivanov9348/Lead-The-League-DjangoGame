from django.urls import path
from match.views import match

app_name = 'match'

urlpatterns = [
    path('match/', match, name='match'),
]
