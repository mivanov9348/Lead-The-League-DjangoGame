from leagues.models import DivisionTeam
from players.models import PlayerAttribute, Player
from teams.models import Team


def get_team_home_data(user):
    team = Team.objects.get(user=user)
    players = Player.objects.filter(team=team)

    player_data = []
    for player in players:
        attributes = PlayerAttribute.objects.filter(player=player).select_related('attribute')
        player_data.append({
            'player': player,
            'attributes': attributes
        })

    division_team = DivisionTeam.objects.get(team=team)
    division = division_team.division
    standings = DivisionTeam.objects.filter(division=division)

    user_team_index = list(standings).index(division_team)

    if user_team_index <= 1:
        centered_standings = standings[:5]
    elif user_team_index >= len(standings) - 2:
        centered_standings = standings[-5:]
    else:
        centered_standings = standings[user_team_index - 2:user_team_index + 3]

    return {
        'team': team,
        'manager_name': team.user.username,
        'player_count': players.count(),
        'player_data': player_data,
        'standings': centered_standings,
    }
