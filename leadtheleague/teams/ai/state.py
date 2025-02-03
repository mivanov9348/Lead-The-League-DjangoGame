from teams.ai.coachAi.coachAi import CoachAI
from teams.ai.releaseAi.ReleaseAi import ReleaseAI
from teams.ai.stadiumAi.stadiumAi import StadiumAI
from teams.ai.transferAi.TransferAi import TransfersAI
from transfers.utils import is_transfer_day
from teams.models import Team

class TeamState:
    @staticmethod
    def process_all_teams(season):
        teams = Team.objects.filter(user__isnull=True).select_related('teamfinance')
        for team in teams:
            state = TeamState(team, season.current_date)
            state.make_decision()

    def __init__(self, team, current_date):
        self.team = team
        self.current_date = current_date
        self.team_finance = getattr(team, 'teamfinance', None)

    def make_decision(self):
        print(f'Making decision for: {self.team.name}')
        if not self.team_finance:
            print(f"{self.team.name}: No financial data available, skipping AI actions.")
            return

        CoachAI.manage_coaches_and_training(self.team)
        # StadiumAI.upgrade_stadiums()

        if is_transfer_day():
            print(f"{self.team.name}: Transfer day detected. Initiating transfer AI actions.")
            ReleaseAI.manage_player_releases(self.team)
            TransfersAI.handle_transfers(self.team, self.team_finance)
        else:
            print(f"{self.team.name}: Not a transfer day. Skipping transfer AI actions.")