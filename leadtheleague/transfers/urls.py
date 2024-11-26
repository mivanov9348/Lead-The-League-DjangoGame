from django.urls import path

from transfers import views

app_name = 'transfers'

urlpatterns = [
    path('transfer_market/', views.transfer_market, name='transfer_market'),
    path('sort_players/', views.sort_players, name='sort_players'),
]
