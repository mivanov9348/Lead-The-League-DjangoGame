from django.contrib import admin
from django.urls import path, include
from accounts.views import welcome_page

urlpatterns = [

    path("admin/", admin.site.urls),
    path('', welcome_page, name='welcome_page'),
    path('accounts/', include('accounts.urls')),
    path('teams/', include('teams.urls', namespace='teams')),
    path('game/', include('game.urls', namespace='game')),
    path('players/', include('players.urls'))
]
