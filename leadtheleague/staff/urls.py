from django.urls import path

from staff.views import staff_market, hire_coach, fire_coach, football_agents, football_agent

app_name = 'staff'

urlpatterns = [
    path('staff_market/', staff_market, name='staff_market'),
    path('hire_coach/', hire_coach, name='hire_coach'),
    path('fire_coach/<int:coach_id>/', fire_coach, name='fire_coach'),
    path('football_agents/', football_agents, name='football_agents'),
    path('football_agent/<int:agent_id>/', football_agent, name='football_agent'),

]
