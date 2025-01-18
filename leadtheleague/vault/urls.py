from django.urls import path

from vault.views import season_stats

app_name = 'vault'

urlpatterns = [
    path('season_stats/', season_stats, name='season_stats'),
]
