from django.db.models import Prefetch
from django.urls import reverse

from players.utils.get_player_stats_utils import get_player_season_stats, get_personal_player_data, \
    get_player_attributes, get_players_season_stats_by_team
from .forms import TeamCreationForm, TeamLogoForm
from players.models import Player, PlayerSeasonStatistic, PlayerAttribute
from teams.models import Team, TeamTactics, Tactics, TeamSeasonStats, TeamPlayer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .utils.generate_team_utils import replace_dummy_team


@login_required
def create_team(request):
    if request.method == 'POST':
        form = TeamCreationForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.user = request.user
            team.is_dummy = False
            team.save()

            if replace_dummy_team(team):
                return redirect('game:home')
            else:
                form.add_error(None, "Not Found Dummy Team")

            return redirect('teams:team_list')
    else:
        form = TeamCreationForm()

    return render(request, 'team/create_team.html', {'form': form})


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
    context = {
        'team': team,
        'season_stats': season_stats,
    }

    return render(request, 'team/team_stats.html', context)

@login_required
@csrf_exempt
def line_up(request):
    try:
        # Получаване на отбора на потребителя
        team = get_object_or_404(Team, user=request.user)
    except AttributeError:
        return redirect("error_page")

    # Вземане на тактиките на отбора
    team_tactics, _ = TeamTactics.objects.get_or_create(team=team)
    tactics = Tactics.objects.all()
    selected_tactic = team_tactics.tactic if team_tactics.tactic else tactics.first()

    # Обработка на GET заявка за промяна на тактика
    if request.method == "GET" and "tactic_id" in request.GET:
        tactic_id = request.GET.get("tactic_id")
        selected_tactic = Tactics.objects.filter(id=tactic_id).first()
        if selected_tactic:
            team_tactics.tactic = selected_tactic
            team_tactics.save()

    # Извличане на данни за всички играчи от отбора
    team_players = team.team_players.select_related('player__position', 'player__nationality').prefetch_related(
        Prefetch(
            'player__season_stats',
            queryset=PlayerSeasonStatistic.objects.select_related('statistic')
        )
    )

    # Получаване на стартовите и резервните играчи от текущата тактика
    starting_players_ids = set(team_tactics.starting_players.values_list('id', flat=True))
    reserve_players_ids = set(team_tactics.reserve_players.values_list('id', flat=True))

    # Създаване на списък с играчи и техните данни
    all_players = []
    for team_player in team_players:
        player = team_player.player
        season_stats = {
            stat.statistic.name: stat.value for stat in player.season_stats.all()
        }
        all_players.append({
            'id': player.id,
            'name': player.name,
            'position': player.position.name if player.position else 'Unknown',
            'position_abbr': player.position.abbreviation if player.position else 'N/A',
            'nationality': player.nationality.name if player.nationality else 'Unknown',
            'nationality_abbr': player.nationality.abbreviation if player.nationality else 'N/A',
            'season_stats': season_stats,
            'is_starting': player.id in starting_players_ids,
            'is_reserve': player.id in reserve_players_ids,
            'image_url': player.image.url if player.image else None,
        })

    # Сортиране на играчите: стартови -> резервни -> останалите
    all_players = sorted(
        all_players,
        key=lambda p: (
            not p['is_starting'],
            not p['is_reserve'],
            not p['position']
        )
    )

    # Подготовка на контекста за предаване към шаблона
    context = {
        "team": team,
        "tactics": tactics,
        "selected_tactic": selected_tactic,
        "players": all_players,  # Коригирано от reservePlayers на players
    }

    return render(request, "team/line_up.html", context)

@login_required
@csrf_exempt
def save_lineup(request):
    if request.method == "POST":
        team = get_object_or_404(Team, user=request.user)
        tactic_id = request.POST.get("tactic_id")
        selected_tactic = get_object_or_404(Tactics, id=tactic_id)

        # Изчистване на текущия състав
        team_tactics, _ = TeamTactics.objects.get_or_create(team=team)
        team_tactics.starting_players.clear()
        team_tactics.reserve_players.clear()
        team_tactics.tactic = selected_tactic

        # Карта за валидиране на тактиката
        tactic_requirements = {
            "GK": selected_tactic.num_goalkeepers,
            "DF": selected_tactic.num_defenders,
            "MF": selected_tactic.num_midfielders,
            "ATT": selected_tactic.num_attackers,
        }
        position_counts = {pos: 0 for pos in tactic_requirements}
        reserve_count = 0

        # Преброяване на играчите
        for key, value in request.POST.items():
            if key.startswith("player_assignment_"):
                player_id = int(key.replace("player_assignment_", ""))
                player = get_object_or_404(Player, id=player_id)

                if value == "starting":
                    position = player.position.abbreviation
                    if position in position_counts:
                        position_counts[position] += 1
                    team_tactics.starting_players.add(player)
                elif value == "reserve":
                    reserve_count += 1
                    team_tactics.reserve_players.add(player)

        # Проверка за резервни играчи
        if reserve_count > 10:
            messages.error(request, "You cannot have more than 10 reserve players.")
            return redirect("teams:line_up")

        # Проверка на стартовия състав спрямо тактиката
        for position, required_count in tactic_requirements.items():
            if position_counts[position] != required_count:
                messages.error(
                    request,
                    f"Your lineup does not match the selected tactic. "
                    f"You need {required_count} {position} players, but you have {position_counts[position]}.",
                )
                return redirect("teams:line_up")

        team_tactics.save()
        messages.success(request, "Lineup successfully saved!")

    return redirect("teams:line_up")


@login_required
def my_team(request):
    team = get_object_or_404(Team, user=request.user)

    if request.method == 'POST':
        form = TeamLogoForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, 'Team logo has been updated!')
            return redirect('my_team')
    else:
        form = TeamLogoForm(instance=team)

    context = {
        'team': team,
        'form': form
    }

    return render(request, 'team/my_team.html', context)
