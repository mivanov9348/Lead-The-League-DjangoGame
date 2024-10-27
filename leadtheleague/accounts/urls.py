from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('welcome/', views.welcome_page, name='welcome_page'),
    path('login/', views.CustomLoginView.as_view(), name='login'),  # Added .as_view()
    path('signup/', views.SignUpView.as_view(), name='signup'),     # Added .as_view()
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', LogoutView.as_view(), name='logout'),           # Added .as_view()
]