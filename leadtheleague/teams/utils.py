import random

from leagues.models import Division, League
from players.utils import generate_team_players
from teams.models import AdjectiveTeamNames, NounTeamNames, Team


def fill_dummy_teams():
    Team.objects.filter(is_dummy=True).delete()

    adjectives = list(AdjectiveTeamNames.objects.values_list('word', flat=True))
    nouns = list(NounTeamNames.objects.values_list('word', flat=True))
    colors = ['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Black', 'White']

    leagues = League.objects.all().order_by('level')

    for league in leagues:
        divisions = Division.objects.filter(league=league).order_by('div_number')

        for division in divisions:
            existing_team_count = Team.objects.filter(division=division).count()
            teams_needed = division.teams_count - existing_team_count

            for _ in range(teams_needed):
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
                    is_dummy=True,
                    division=division
                )

                generate_team_players(team)
