from django.urls import path
from stadium.views import stadium, purchase_tier

app_name = 'stadium'

urlpatterns = [
    path('stadium/', stadium, name='stadium'),
    path('purchase_tier/', purchase_tier, name='purchase_tier'),

]
