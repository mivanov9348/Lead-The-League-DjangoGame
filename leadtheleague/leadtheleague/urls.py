from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from accounts.views import welcome_page
from leadtheleague import settings

urlpatterns = [

    path("admin/", admin.site.urls),
    path('', welcome_page, name='welcome_page'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('teams/', include('teams.urls', namespace='teams')),
    path('game/', include('game.urls', namespace='game')),
    path('players/', include('players.urls', namespace='players')),
    path('leagues/', include('leagues.urls', namespace='leagues')),
    path('fixtures/', include('fixtures.urls', namespace='fixtures')),
    path('messaging/', include('messaging.urls', namespace='messaging')),
    path('match/', include('match.urls', namespace='match')),
    path('transfers/', include('transfers.urls', namespace='transfers')),
    path('finance/', include('finance.urls', namespace='finance')),
    path('staff/', include('staff.urls', namespace='staff')),
]

if settings.DEBUG:  # Не забравяйте да добавите този блок за сервиране на медийни файлове по време на разработка
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
