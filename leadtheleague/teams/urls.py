from django.conf.urls.static import static
from django.urls import path
from leadtheleague import settings
from .views import squad, team_stats, line_up, my_team, save_lineup, training, train_coach

app_name = 'teams'

urlpatterns = [
    path('squad/', squad, name='squad'),
    path("line_up/", line_up, name="line_up"),
    path('save_lineup/', save_lineup, name='save_lineup'),
    path('training/', training, name='training'),
    path('train_coach/<int:coach_id>/', train_coach, name='train_coach'),
    path('team-stats/', team_stats, name='team_stats'),
    path('my_team/', my_team, name='my_team'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
