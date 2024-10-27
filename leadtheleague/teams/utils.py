import random

from leagues.models import Division, League, DivisionTeam
from players.utils import generate_team_players
from teams.models import AdjectiveTeamNames, NounTeamNames, Team


def fill_dummy_teams():
    Team.objects.filter(is_dummy=True).delete()
    DivisionTeam.objects.filter(is_dummy=True).delete()

    adjectives = list(AdjectiveTeamNames.objects.values_list('word', flat=True))
    nouns = list(NounTeamNames.objects.values_list('word', flat=True))
    colors = ['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Black', 'White']

    leagues = League.objects.all().order_by('level')

    for league in leagues:
        divisions = Division.objects.filter(league=league).order_by('div_number')

        for division in divisions:
            team_count = DivisionTeam.objects.filter(division=division).count()

            while team_count < division.teams_count:
                if random.choice([True, False]):
                    name = f'{random.choice(adjectives)} {random.choice(nouns)}'
                else:
                    name = random.choice(nouns)

                color = random.choice(colors)

                team = Team.objects.create(
                    name=name,
                    abbr=name[:3].upper(),
                    color=color,
                    user=None,
                    is_dummy=True
                )

                DivisionTeam.objects.create(
                    division=division,
                    team=team,
                    is_dummy=True
                )

                generate_team_players(team)
                team_count += 1
