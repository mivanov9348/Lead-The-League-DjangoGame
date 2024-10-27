from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView
from accounts.forms import CustomUserCreationForm
from teams.models import Team
from django.shortcuts import render
from game.models import Season  # Import your Season model
from datetime import date


# Create your views here.
def welcome_page(request):
    return render(request, 'home/welcome.html')


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('home')  # Redirect to mainmenu initially
    template_name = 'accounts/signup.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)

        # Check if the user already has a team
        if not Team.objects.filter(user=user).exists():  # Use manager if that's your field name
            return redirect('teams:create_team')  # Redirect to create_team if no team exists

        return redirect(self.success_url)  # Redirect to mainmenu if a team exists

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = False


def get_success_url(self):
    if not Team.objects.filter(user=self.request.user).exists():
        return reverse_lazy('teams:create_team')
    return reverse_lazy('game:home')


@staff_member_required
def admin_dashboard(request):
    current_year = date.today().year
    seasons = Season.objects.filter(year=current_year)

    # Get the next available season number
    season_number = seasons.count() + 1  # Start from 1 for the new season

    if request.method == "POST":
        year = int(request.POST.get("year"))
        season_number = int(request.POST.get("season_number"))
        start_date = request.POST.get("start_date")

        # Check if season already exists
        if not Season.objects.filter(year=year, season_number=season_number).exists():
            # Create new season
            Season.objects.create(year=year, season_number=season_number, start_date=start_date)
            # Optionally, redirect or provide a success message
        else:
            # Handle the error: season already exists
            pass

    return render(request, 'accounts/admin_dashboard.html', {
        'seasons': seasons,
        'current_year': current_year,
        'season_number': season_number,
    })
