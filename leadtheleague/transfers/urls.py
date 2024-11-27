from django.urls import path

from transfers import views

app_name = 'transfers'

urlpatterns = [
    path('transfer_market/', views.transfer_market, name='transfer_market'),
    path('make_offer-purchase/', views.make_offer, name='make_offer'),
]
