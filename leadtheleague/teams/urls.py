from django.conf.urls.static import static
from django.urls import path
from leadtheleague import settings
from .views import create_team, squad, team_stats, line_up, my_team, save_lineup

app_name = 'teams'

urlpatterns = [
    path('create_team/', create_team, name='create_team'),
    path('squad/', squad, name='squad'),
    path("line_up/", line_up, name="line_up"),
    path('save_lineup/', save_lineup, name='save_lineup'),  # Добави този ред
    path('team-stats/', team_stats, name='team_stats'),
    path('my_team/', my_team, name='my_team'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
