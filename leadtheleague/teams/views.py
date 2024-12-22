from itertools import chain
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from fixtures.models import LeagueFixture, CupFixture
from fixtures.utils import get_team_fixtures_for_current_season
from game.models import Season
from players.utils.get_player_stats_utils import get_player_season_stats, get_personal_player_data, \
    get_player_attributes
from staff.models import Coach
from players.models import Player, PlayerSeasonStatistic, PlayerAttribute
from teams.models import Team, TeamTactics, Tactics, TeamPlayer, TeamFinance
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .utils.get_team_stats_utils import get_team_data, get_fixtures_by_team_and_type
from .utils.training_utils import player_training


def get_sort_field(sort_by):
    valid_sort_fields = {
        'shirt_number': 'shirt_number',
        'name': 'player__first_name',
        'positionabbr': 'player__position__id',
        'nationalityabbr': 'player__nationality__abbreviation',
        'handling': 'player__playerattribute__handling',
        'reflexes': 'player__playerattribute__reflexes',
        'Finishing': 'player__playerattribute__Finishing',
        'shooting': 'player__playerattribute__shooting',
        'technique': 'player__playerattribute__technique',
        'passing': 'player__playerattribute__passing',
        'crossing': 'player__playerattribute__crossing',
        'tackling': 'player__playerattribute__tackling',
        'strength': 'player__playerattribute__strength',
        'determination': 'player__playerattribute__determination',
        'ball_control': 'player__playerattribute__ball_control',
        'dribbling': 'player__playerattribute__dribbling',
        'speed': 'player__playerattribute__speed',
        'vision': 'player__playerattribute__vision',
        'work_rate': 'player__playerattribute__work_rate',
    }

    return valid_sort_fields.get(sort_by, 'player__first_name')


def squad(request):
    team = get_object_or_404(Team, user=request.user)

    sort_by = request.GET.get('sort_by', 'name')
    order = request.GET.get('order', 'asc')

    sort_field = get_sort_field(sort_by)

    if order == 'desc':
        sort_field = f'-{sort_field}'

    team_players = TeamPlayer.objects.filter(team=team).select_related('player').prefetch_related(
        Prefetch(
            'player__season_stats',
            queryset=PlayerSeasonStatistic.objects.select_related('statistic')
        ),
        Prefetch(
            'player__playerattribute_set',
            queryset=PlayerAttribute.objects.select_related('attribute')
        )
    ).order_by(sort_field)

    players_data = []
    for team_player in team_players:
        player = team_player.player
        players_data.append({
            'personal_info': get_personal_player_data(player),
            'shirt_number': team_player.shirt_number,
            'attributes': get_player_attributes(player),
            'stats': get_player_season_stats(player)
        })

    print(players_data)

    context = {
        'team': team,
        'players_data': players_data,
        'current_sort': sort_by,
        'current_order': order
    }
    return render(request, 'teams/squad.html', context)


def team_stats(request, team_id):
    team_data = get_team_data(team_id)

    players = TeamPlayer.objects.filter(team_id=team_id).select_related('player', 'player__position',
                                                                        'player__nationality')
    players_data = [get_personal_player_data(player.player) for player in players]

    context = {
        'team': team_data,
        'players': players_data,
    }
    return render(request, 'teams/team_stats.html', context)


@login_required
@csrf_exempt
def line_up(request):
    try:
        team = get_object_or_404(Team, user=request.user)
    except AttributeError:
        return redirect("error_page")

    team_tactics, _ = TeamTactics.objects.get_or_create(team=team)
    tactics = Tactics.objects.all()
    selected_tactic = team_tactics.tactic if team_tactics.tactic else tactics.first()

    if request.method == "GET" and "tactic_id" in request.GET:
        tactic_id = request.GET.get("tactic_id")
        selected_tactic = Tactics.objects.filter(id=tactic_id).first()
        if selected_tactic:
            team_tactics.tactic = selected_tactic
            team_tactics.save()

    team_players = team.team_players.filter(player__is_youth=False).select_related(
        'player__position', 'player__nationality'
    ).prefetch_related(
        Prefetch(
            'player__season_stats',
            queryset=PlayerSeasonStatistic.objects.select_related('statistic')
        )
    )

    starting_players_ids = set(team_tactics.starting_players.values_list('id', flat=True))
    reserve_players_ids = set(team_tactics.reserve_players.values_list('id', flat=True))

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

    all_players = sorted(
        all_players,
        key=lambda p: (
            not p['is_starting'],
            not p['is_reserve'],
            not p['position']
        )
    )

    context = {
        "teams": team,
        "tactics": tactics,
        "selected_tactic": selected_tactic,
        "players": all_players,
    }

    return render(request, "teams/line_up.html", context)


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
                player = get_object_or_404(Player, id=player_id, is_youth=False)  # Изключваме младежите

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


def training(request):
    team = get_object_or_404(Team, user=request.user)

    coaches = Coach.objects.filter(team=team)
    players_qs = TeamPlayer.objects.filter(team=team, player__is_active=True).select_related('player')

    players_data = [get_personal_player_data(player.player) for player in players_qs]

    return render(request, 'teams/training.html', {'coaches': coaches, 'players': players_data})


@csrf_exempt
def train_coach(request, coach_id):
    try:
        if request.method == 'POST':
            coach = get_object_or_404(Coach, id=coach_id)
            result = player_training(coach, None)
            print(result["details"])  # Отпечатва детайлите в конзолата
            return JsonResponse({"success": True, "impact": result["training_impact"]})
        else:
            return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)
    except Exception as e:
        print(f"Error in train_coach: {str(e)}")  # Отпечатва грешката
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@login_required
def schedule(request):
    user_team = Team.objects.filter(user=request.user).first()

    fixtures_by_type = get_fixtures_by_team_and_type(user_team)

    all_fixtures = list(chain(
        fixtures_by_type.get("league", []),
        fixtures_by_type.get("cup", []),
        fixtures_by_type.get("euro", [])
    ))
    fixture_dict = {}

    for fixture in all_fixtures:
        fixture_date = fixture.date.strftime("%Y-%m-%d") if fixture.date else "No Date"
        if fixture_date not in fixture_dict:
            fixture_dict[fixture_date] = []

        fixture_info = {
            "date": fixture.date,
            "round": getattr(fixture, 'round_number', None),
            "home_away": "Home" if fixture.home_team == user_team else "Away",
            "opponent": fixture.away_team if fixture.home_team == user_team else fixture.home_team,
            "time": fixture.match_time.strftime("%H:%M") if fixture.match_time else "No Time",
            "type": "League" if isinstance(fixture, LeagueFixture) else "Cup",
        }
        fixture_dict[fixture_date].append(fixture_info)

    sorted_fixtures = sorted(fixture_dict.items(), key=lambda x: x[0])

    fixture_list = []
    for date, fixtures_on_date in sorted_fixtures:
        fixture_list.append({
            "date": date,
            "matches": fixtures_on_date[:10],
        })

    context = {
        'fixtures': fixture_list,
    }

    return render(request, 'teams/schedule.html', context)