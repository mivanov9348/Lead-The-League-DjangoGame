from django.conf.urls.static import static
from django.urls import path
from leadtheleague import settings
from .views import squad, team_stats, line_up, save_lineup, training, schedule, train_team, auto_lineup

app_name = 'teams'

urlpatterns = [
    path('squad/', squad, name='squad'),
    path("line_up/", line_up, name="line_up"),
    path('save_lineup/', save_lineup, name='save_lineup'),
    path('auto_lineup/', auto_lineup, name='auto_lineup'),
    path('training/', training, name='training'),
    path('train_team/<int:team_id>/', train_team, name='train_team'),
    path('team_stats/<int:team_id>/', team_stats, name='team_stats'),
    path('schedule/', schedule, name='schedule'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
