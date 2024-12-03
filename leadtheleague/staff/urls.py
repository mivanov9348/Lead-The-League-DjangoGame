from django.urls import path

from staff.views import staff_market


app_name = 'staff'

urlpatterns = [
    path('staff_market/', staff_market, name='staff_market'),
]