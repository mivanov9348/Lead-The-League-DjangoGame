from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import SignUpView, CustomLoginView, welcome_page

urlpatterns = [
    path('welcome/', welcome_page, name='welcome_page'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
]