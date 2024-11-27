from django.conf.urls.static import static
from django.urls import path
from leadtheleague import settings
from .views import create_team, squad, team_stats, line_up, lineup_add_player, lineup_remove_player, my_team

app_name = 'teams'

urlpatterns = [
    path('create_team/', create_team, name='create_team'),
    path('squad/', squad, name='squad'),
    path("line_up/", line_up, name="line_up"),
    path("lineup/add-player/", lineup_add_player, name="lineup_add_player"),
    path("lineup/remove-player/", lineup_remove_player, name="lineup_remove_player"),
    path('team-stats/', team_stats, name='team_stats'),
    path('my_team/', my_team, name='my_team'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
