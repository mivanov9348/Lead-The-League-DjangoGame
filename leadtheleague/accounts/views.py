from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth import login
from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView
from accounts.forms import CustomUserCreationForm
from fixtures.models import Fixture
from game.utils import get_current_season, create_new_season
from leagues.models import League, DivisionTeam, Division
from leagues.utils import get_standings_for_division, get_leagues_and_divisions
from teams.models import Team
from django.shortcuts import render
from datetime import date, datetime, timedelta
from django.http import HttpResponseRedirect


def welcome_page(request):
    return render(request, 'home/welcome.html')


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('home')
    template_name = 'accounts/signup.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)

        if not Team.objects.filter(user=user).exists():
            return redirect('teams:create_team')

        return redirect(self.success_url)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = False


def get_success_url(self):
    if not Team.objects.filter(user=self.request.user).exists():
        return reverse_lazy('teams:create_team')
    return reverse_lazy('game:home')


@staff_member_required()
def admin_dashboard(request):
    current_year = date.today().year
    season = get_current_season(current_year)
    season_number = season.season_number if season else None

    leagues = get_leagues_and_divisions()

    selected_division_id = request.GET.get('division')
    selected_round = request.GET.get('round')

    selected_division = int(selected_division_id) if selected_division_id else None
    all_standings = []
    fixtures = []
    rounds = []

    if selected_division:
        all_standings = DivisionTeam.objects.filter(division=selected_division)

        # Get all fixtures for the selected division
        division_fixtures = Fixture.objects.filter(division=selected_division)

        # Get distinct rounds in this division
        rounds = division_fixtures.values_list('round_number', flat=True).distinct()

        # Filter fixtures by selected round if any
        if selected_round:
            fixtures = division_fixtures.filter(round_number=selected_round)
        else:
            fixtures = division_fixtures  # No round selected, show all

    return render(request, 'accounts/admin_dashboard.html', {
        'current_year': current_year,
        'season_number': season_number,
        'leagues': leagues,
        'standings': all_standings,
        'fixtures': fixtures,
        'selected_division': selected_division_id,
        'selected_round': selected_round,
        'rounds': rounds,
    })


@staff_member_required()
def create_season(request):
    if request.method == 'POST':
        year = request.POST.get('year')
        season_number = request.POST.get('season_number')
        start_date_str = request.POST.get('start_date')
        print(
            f"Получени данни: Година - {year}, Номер на сезона - {season_number}, Дата на начало - {start_date_str}")

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        create_new_season(year, season_number, start_date)

        return HttpResponseRedirect(reverse('accounts:admin_dashboard'))

    return render(request, 'accounts/admin_dashboard.html', {
        'error': 'Invalid Session!'
    })
