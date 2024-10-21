from django.shortcuts import render, redirect

# Create your views here.
def welcome_page(request):
    return render(request, 'home/welcome.html')