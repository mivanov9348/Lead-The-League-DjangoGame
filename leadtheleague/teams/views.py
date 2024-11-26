import os
from django.db.models import Prefetch
from django.templatetags.static import static
from leadtheleague import settings
from players.utils.get_player_stats_utils import get_player_season_stats, get_personal_player_data, \
    get_player_attributes
from .forms import TeamCreationForm
from players.models import Player, PlayerSeasonStatistic, PlayerAttribute
from teams.models import Team, TeamTactics, Tactics, TeamSeasonStats, TeamPlayer
from django.contrib.auth.decorators import login_required
from .utils import replace_dummy_team, create_team_performance_chart, \
    create_position_template
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required


@login_required
def create_team(request):
    if request.method == 'POST':
        form = TeamCreationForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.user = request.user
            team.is_dummy = False  # Ensure the team is not a dummy
            team.save()

            # Replace a dummy team with the newly created team
            if replace_dummy_team(team):
                return redirect('game:home')
            else:
                form.add_error(None, "No dummy team found to replace.")
    else:
        form = TeamCreationForm()

    context = {
        'form': form,
    }
    return render(request, 'team/create_team.html', context)


def squad(request):
    team = get_object_or_404(Team, user=request.user)

    # Вземаме всички играчи на отбора с техните статистики и други свързани обекти наведнъж
    team_players = TeamPlayer.objects.filter(team=team).select_related('player').prefetch_related(
        Prefetch(
            'player__season_stats',
            queryset=PlayerSeasonStatistic.objects.select_related('statistic')
        ),
        Prefetch(
            'player__playerattribute_set',
            queryset=PlayerAttribute.objects.select_related('attribute')
        )
    )

    # Извличаме данни за всеки играч
    players_data = []
    for team_player in team_players:
        player = team_player.player
        players_data.append({
            'personal_info': get_personal_player_data(player),
            'shirt_number': team_player.shirt_number,
            'attributes': get_player_attributes(player),
            'stats': get_player_season_stats(player)
        })

    # Подготвяме контекста за шаблона
    context = {
        'team': team,
        'players_data': players_data
    }
    return render(request, 'team/squad.html', context)


def team_stats(request):
    team = Team.objects.get(id=request.user.team.id)  # Assuming the user is linked to a team
    season_stats = TeamSeasonStats.objects.filter(team=team)

    img = create_team_performance_chart(season_stats, team.name)

    context = {
        'team': team,
        'season_stats': season_stats,
        'img': img
    }

    return render(request, 'team/team_stats.html', context)


@login_required
@csrf_exempt
def line_up(request):
    try:
        team = get_object_or_404(Team, user=request.user)
    except AttributeError:
        return redirect("error_page")

    team_tactics, _ = TeamTactics.objects.get_or_create(team=team)
    tactics = Tactics.objects.all()
    selected_tactic = None

    if request.method == "GET" and "tactic_id" in request.GET:
        tactic_id = request.GET.get("tactic_id")
        selected_tactic = Tactics.objects.filter(id=tactic_id).first()
        if selected_tactic:
            if team_tactics:
                team_tactics.starting_players.clear()
            team_tactics.tactic = selected_tactic
            team_tactics.save()

    if selected_tactic is None:
        selected_tactic = team_tactics.tactic

    starting_players = team_tactics.starting_players.all() if team_tactics else []
    reserve_players = Player.objects.filter(
        id__in=TeamPlayer.objects.filter(team=team).values_list('player', flat=True)).exclude(
        id__in=[player.id for player in starting_players])
    position_template = create_position_template(selected_tactic, starting_players)

    context = {
        "team": team,
        "tactics": tactics,
        "selected_tactic": selected_tactic,
        "starting_players": starting_players,
        "reservePlayers": reserve_players,
        "position_template": position_template,
    }

    return render(request, "team/line_up.html", context)


def lineup_add_player(request):
    if request.method == "POST":
        player_id = request.POST.get("player_id")
        if not player_id:
            messages.error(request, "No player selected.")
            return redirect("teams:line_up")

        # Намери играча
        player = get_object_or_404(Player, id=player_id)

        try:
            # Намери отбора на логнатия потребител
            team = get_object_or_404(Team, user=request.user)
        except AttributeError:
            messages.error(request, "You do not have a team.")
            return redirect("teams:line_up")

        # Намери или създай тактиката на отбора
        team_tactics, created = TeamTactics.objects.get_or_create(team=team)

        # Увери се, че тактиката е зададена
        if not team_tactics.tactic:
            messages.error(request, "Please select a tactic before adding players.")
            return redirect("teams:line_up")

        # Извлечи информацията за броя позиции от тактиката
        tactic = team_tactics.tactic

        # Брои играчите в стартовия състав за всяка позиция
        position_counts = {
            "goalkeeper": team_tactics.starting_players.filter(position__name="Goalkeeper").count(),
            "defender": team_tactics.starting_players.filter(position__name="Defender").count(),
            "midfielder": team_tactics.starting_players.filter(position__name="Midfielder").count(),
            "attacker": team_tactics.starting_players.filter(position__name="Attacker").count(),
        }

        # Проверява дали добавянето на играча ще надвиши лимита
        if player.position.name == "Goalkeeper" and position_counts["goalkeeper"] >= tactic.num_goalkeepers:
            messages.error(request, "You cannot add more goalkeepers to the starting lineup.")
        elif player.position.name == "Defender" and position_counts["defender"] >= tactic.num_defenders:
            messages.error(request, "You cannot add more defenders to the starting lineup.")
        elif player.position.name == "Midfielder" and position_counts["midfielder"] >= tactic.num_midfielders:
            messages.error(request, "You cannot add more midfielders to the starting lineup.")
        elif player.position.name == "Attacker" and position_counts["attacker"] >= tactic.num_attackers:
            messages.error(request, "You cannot add more forwards to the starting lineup.")
        else:
            # Добави играча в стартовия състав
            team_tactics.starting_players.add(player)
            messages.success(request, f"{player.first_name} {player.last_name} added to the starting lineup.")
        return redirect("teams:line_up")


def lineup_remove_player(request):
    if request.method == "POST":
        player_id = request.POST.get("player_id")
        if not player_id:
            messages.error(request, "No player selected.")
            return redirect("teams:line_up")

        # Намери играча
        player = get_object_or_404(Player, id=player_id)

        # Намери отбора на логнатия потребител
        try:
            team = get_object_or_404(Team, user=request.user)
        except AttributeError:
            messages.error(request, "You do not have a team.")
            return redirect("teams:line_up")

        # Намери тактиката на отбора
        team_tactics = TeamTactics.objects.filter(team=team).first()
        if not team_tactics or player not in team_tactics.starting_players.all():
            messages.warning(request, f"{player.first_name} {player.last_name} is not in the starting lineup.")
        else:
            # Премахни играча от стартовия състав
            team_tactics.starting_players.remove(player)
            player.save()
            messages.success(request, f"{player.first_name} {player.last_name} removed from the starting lineup.")

        return redirect("teams:line_up")


def logos(request):
    # Изграждане на пътя до директорията 'static/logos'
    logos_path = os.path.join(settings.BASE_DIR, 'static', 'logos')

    # Проверка дали директорията съществува
    if not os.path.exists(logos_path):
        return render(request, 'teams/logos.html', {'error': 'Директорията с логота не съществува.'})

    # Получаване на списък с файлове
    logo_files = [
        static(f'logos/{f}') for f in os.listdir(logos_path)
        if os.path.isfile(os.path.join(logos_path, f))
    ]

    print(logo_files)
    # Подаване на логотата към шаблона
    return render(request, 'team/logos.html', {'logos': logo_files})
