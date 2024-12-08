from django.urls import path
from stadium.views import stadium

app_name = 'stadium'

urlpatterns = [
    path('stadium/', stadium, name='stadium'),
]
