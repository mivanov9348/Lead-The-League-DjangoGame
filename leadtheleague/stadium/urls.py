from django.urls import path
from stadium.views import stadium, buy_tier

app_name = 'stadium'

urlpatterns = [
    path('stadium/', stadium, name='stadium'),
    path("buy_tier/<int:tier_id>/", buy_tier, name="buy_tier"),
]
