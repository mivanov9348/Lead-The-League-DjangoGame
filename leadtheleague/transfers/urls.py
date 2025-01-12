from django.urls import path
from transfers import views

app_name = 'transfers'

urlpatterns = [
    path('transfer_history/', views.transfer_history, name='transfer_history'),
    path('negotiations/', views.negotiations, name='negotiations'),
    path('check_new_offers/', views.check_new_offers, name='check_new_offers'),
    path('accept_transfer/', views.accept_transfer, name='accept_transfer'),
    path('reject_transfer/', views.reject_transfer, name='reject_transfer'),
    path('send_offer/<int:player_id>/', views.send_offer, name='send_offer'),
]
