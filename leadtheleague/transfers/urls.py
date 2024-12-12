from django.urls import path
from transfers import views

app_name = 'transfers'

urlpatterns = [
    path('free_agent_market/', views.free_agent_market, name='free_agent_market'),
    path('transfer_history/', views.transfer_history, name='transfer_history'),
    path('negotiations/', views.negotiations, name='negotiations'),
    path('accept_transfer/', views.accept_transfer, name='accept_transfer'),
    path('reject_transfer/', views.reject_transfer, name='reject_transfer'),
    path('make_offer-purchase/', views.get_free_agent, name='get_free_agent'),
    path('check_balance/', views.check_balance, name='check_balance'),

]
