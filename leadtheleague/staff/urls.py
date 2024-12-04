from django.urls import path

from staff.views import staff_market, hire_coach

app_name = 'staff'

urlpatterns = [
    path('staff_market/', staff_market, name='staff_market'),
    path('hire_coach/', hire_coach, name='hire_coach'),

]