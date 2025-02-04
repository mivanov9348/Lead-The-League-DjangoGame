from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from accounts.views import welcome
from leadtheleague import settings

urlpatterns = [

    path("admin/", admin.site.urls),
    path('', welcome, name='welcome'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('teams/', include('teams.urls', namespace='teams')),
    path('game/', include('game.urls', namespace='game')),
    path('players/', include('players.urls', namespace='players')),
    path('leagues/', include('leagues.urls', namespace='leagues')),
    path('messaging/', include('messaging.urls', namespace='messaging')),
    path('match/', include('match.urls', namespace='match')),
    path('transfers/', include('transfers.urls', namespace='transfers')),
    path('finance/', include('finance.urls', namespace='finance')),
    path('staff/', include('staff.urls', namespace='staff')),
    path('stadium/', include('stadium.urls', namespace='stadium')),
    path('cups/', include('cups.urls', namespace='cups')),
    path('europeancups/', include('europeancups.urls', namespace='europeancups')),
    path('vault/', include('vault.urls', namespace='vault')),
    path('chat/', include('chat.urls', namespace='chat'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
