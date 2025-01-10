import json
from datetime import date
from itertools import chain
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from fixtures.models import LeagueFixture
from game.utils.get_season_stats_utils import get_current_season
from leagues.models import LeagueTeams
from players.utils.get_player_stats_utils import get_personal_player_data, get_player_attributes, get_player_stats
from players.utils.update_player_stats_utils import update_player_price
from staff.models import Coach
from players.models import Player, PlayerSeasonStatistic, PlayerAttribute
from teams.models import Team, TeamTactics, Tactics, TeamPlayer, TeamFinance, TrainingImpact, TeamSeasonAnalytics
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .utils.get_team_stats_utils import get_team_data, get_fixtures_by_team_and_type
from .utils.lineup_utils import validate_lineup, auto_select_starting_lineup
from .utils.team_analytics_utils import get_team_analytics


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
    current_season = get_current_season()

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
            'stats': get_player_stats(player, current_season)
        })
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

    team_tactics, created = TeamTactics.objects.get_or_create(team=team)

    if not team_tactics.tactic:
        default_tactic = Tactics.objects.first()  # Избери първата тактика по подразбиране
        team_tactics.tactic = default_tactic
        team_tactics.save()

    selected_tactic = team_tactics.tactic

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
        "tactics": Tactics.objects.all(),
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
        selected_players = request.POST.get("selected_players", "")
        selected_players_ids = selected_players.split(",")  # Превърни в списък

        try:
            selected_players_ids = [int(player_id) for player_id in selected_players_ids if player_id.isdigit()]

            players = Player.objects.filter(id__in=selected_players_ids)

            if players.count() != len(selected_players_ids):
                raise ValueError("Some selected players are invalid.")

            errors = validate_lineup(players, selected_tactic)
            if errors:
                raise ValueError("; ".join(errors))

            existing_team_tactics = TeamTactics.objects.filter(team=team)
            if existing_team_tactics.exists():
                existing_team_tactics.delete()

            team_tactics = TeamTactics.objects.create(team=team, tactic=selected_tactic)

            team_tactics.starting_players.set(players)
            team_tactics.save()

            return JsonResponse({"success": True, "message": "Lineup saved successfully!"})

        except ValueError as e:
            return JsonResponse({"success": False, "message": str(e)})
        except Exception as e:
            return JsonResponse({"success": False, "message": "An error occurred while saving the lineup."})

    return JsonResponse({"success": False, "message": "Invalid request."})


@csrf_exempt
def auto_lineup(request):
    if request.method == "POST":
        try:
            user_team = Team.objects.filter(user=request.user).first()
            auto_select_starting_lineup(user_team)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})
    return JsonResponse({"success": False, "message": "Invalid request method."})


def training(request):
    user_team = Team.objects.filter(user=request.user).first()

    coaches = Coach.objects.filter(team=user_team)

    players_qs = TeamPlayer.objects.filter(team=user_team, player__is_active=True).select_related('player')

    players_data = []
    for player in players_qs:
        attributes = get_player_attributes(player.player)
        players_data.append({
            'id': player.player.id,
            'first_name': player.player.first_name,
            'last_name': player.player.last_name,
            'age': player.player.age,
            'position': player.player.position.name if player.player.position else "-",
            'image_url': player.player.image.url if player.player.image else None,
            'attributes': attributes,
        })

    return render(request, 'teams/training.html', {'coaches': coaches, 'players': players_data, 'team': user_team,
                                                   })


def train_team(request, team_id):
    if request.method == "POST":
        try:
            team = Team.objects.get(id=team_id)
            coach = team.coach

            if not coach:
                return JsonResponse({"success": False, "error": "No coach assigned to the team."})

            data = json.loads(request.body)
            selected_attributes = data.get("selectedAttributes", {})

            if not selected_attributes:
                return JsonResponse({"success": False, "error": "No selected attributes provided."})

            team_players = TeamPlayer.objects.filter(team=team)
            players = [team_player.player for team_player in team_players]
            changes = []
            today = date.today()

            for player in players:
                selected_attribute = selected_attributes.get(str(player.id))
                if not selected_attribute:
                    changes.append({
                        "player": f"{player.first_name} {player.last_name}",
                        "message": "No attribute selected",
                    })
                    continue  # Skip if no attribute was selected for the player

                # Check if the player was trained today
                if TrainingImpact.objects.filter(player=player, coach=coach, date__date=today).exists():
                    changes.append({
                        "player": f"{player.first_name} {player.last_name}",
                        "attribute": selected_attribute,
                        "message": f"{player.first_name} has already been trained today",
                    })
                    continue

                player_attribute = player.playerattribute_set.filter(attribute__name=selected_attribute).first()
                if player_attribute:
                    progress_increase = round(min(0.1 + (float(coach.rating) ** 0.5) / 10.0, 0.5), 2)
                    player_attribute.progress += progress_increase

                    if player_attribute.progress >= 1.0:
                        player_attribute.value += 1
                        player_attribute.progress -= 1.0

                    player_attribute.save()

                    # Log the training in TrainingImpact
                    TrainingImpact.objects.create(
                        player=player,
                        coach=coach,
                        training_impact=progress_increase,
                        notes=f"Trained {player_attribute.attribute.name}"
                    )

                    changes.append({
                        "player": f"{player.first_name} {player.last_name}",
                        "attribute": player_attribute.attribute.name,
                        "new_value": player_attribute.value,
                        "progress": round(player_attribute.progress, 2),
                        "message": "Training completed successfully",
                    })
                    update_player_price(player)

            return JsonResponse({"success": True, "changes": changes})
        except Team.DoesNotExist:
            return JsonResponse({"success": False, "error": "Team not found."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})


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


def all_teams(request):
    # Зареждане на данни с връзка към лигата
    the_top_30 = get_team_analytics(
        limit=30,
        order_by=['-points', '-goalscored', 'goalconceded', '-wins']
    ).select_related('team__league_teams__league_season__league')

    return render(request, 'teams/all_teams.html', {'teams': the_top_30})
