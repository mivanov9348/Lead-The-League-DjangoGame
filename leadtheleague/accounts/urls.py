from django.urls import path
from .views import welcome_page

urlpatterns = [
    path('welcome/', welcome_page, name='welcome_page')
]