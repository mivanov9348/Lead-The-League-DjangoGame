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
        # Get divisions within the league
        divisions = Division.objects.filter(league=league).order_by('div_number')

        # Iterate through each division
        for division in divisions:
            # Check how many dummy teams already exist in this division
            team_count = Team.objects.filter(division=division, is_dummy=True).count()

            # Create dummy teams until the desired count is reached
            while team_count < division.teams_count:
                # Generate a random name for the team
                if random.choice([True, False]):
                    name = f'{random.choice(adjectives)} {random.choice(nouns)}'
                else:
                    name = random.choice(nouns)

                color = random.choice(colors)

                # Create a new dummy team associated with the current division
                team = Team.objects.create(
                    name=name,
                    abbr=name[:3].upper(),
                    color=color,
                    user=None,  # Assuming dummy teams have no associated user
                    is_dummy=True,
                    division=division  # Set the division directly here
                )

                # Call the function to generate players for the created team
                generate_team_players(team)

                # Increment the team count
                team_count += 1
