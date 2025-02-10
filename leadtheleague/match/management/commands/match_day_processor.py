import datetime
from django.core.management import BaseCommand

from chat.utils.cryptography_utils import encrypt_message, decrypt_message
from game.models import MatchSchedule
from game.utils.get_season_stats_utils import get_current_season
from game.utils.schedule_utils import advance_day

from match.utils.match.processing import match_day_processor

class Command(BaseCommand):
    help = 'Processes today\'s match day.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting match day processing...")
        try:
            overall_start_time = datetime.datetime.now()
            print(f"Overall process started at: {overall_start_time}")

            days_step = 6

            season = get_current_season()

            for _ in range(days_step):
                advance_day()

                season.refresh_from_db()
                current_date = season.current_date
                print(f"Processing matches for date: {current_date}")

                match_days = MatchSchedule.objects.filter(season=season, date=current_date, is_played=False).exclude(
                    event_type='transfer'
                )

                if not match_days.exists():
                    print(f"No matches found for {current_date}, skipping.")
                    continue

                for match_day in match_days:
                    start_time = datetime.datetime.now()
                    print(f"Processing match: {match_day} at {start_time}")

                    match_day_processor(match_day.date)

                    end_time = datetime.datetime.now()
                    duration = end_time - start_time
                    print(f"Finished processing match: {match_day} at {end_time}, Duration: {duration}")

                if current_date >= season.end_date:
                    print("Season has ended. Stopping process.")
                    break

            overall_end_time = datetime.datetime.now()
            overall_duration = overall_end_time - overall_start_time
            print(f"Overall process finished at: {overall_end_time}, Total duration: {overall_duration}")

        except Exception as e:
            print(f'Error when processing: {e}')

        # first_name = get_random_first_name('Eastern Europe','Bulgaria')
        # print(first_name)
        # generate_random_player()
        # team = Team.objects.filter(id=12533).first()
        # team_income(team, 2000000, "Test")

        # matches = Match.objects.filter(match_date='2025-03-11')
        # for match in matches:
        #     team_match_profit(match.home_team, match, 2000000, 'test')

        # current_season = get_current_season()
        # df = process_league_season_data(current_season)
        #
        # if df is not None:
        #     # Визуализираме точките
        #     plot_team_points(df)
        #
        #     # Визуализираме отбелязаните голове
        #     plot_goals_scored(df)
        #
        #     # Визуализираме точките спрямо разлика в головете
        #     plot_points_vs_goal_difference(df)

        # match = Match.objects.filter(id = 170168).first()
        # process_match(match)

        # success_rates = []
        # for i in range(0, 50):
        #     print('----------------------------')
        #     event = get_random_match_event()
        #     print(f'Event: {event}')
        #     players = Player.objects.all()
        #     player = random.choice(players)
        #     print(f'Player: {player.first_name} {player.last_name} - {player.position.name}')
        #     success = calculate_event_success_rate(event, player)
        #     print(f'Success: {success}')
        #     success_rates.append(success)
        #     event_result = get_event_result(event, success)
        #     print(f'event result: {event_result.event_result}')
        #
        # print(f'average for 50: {average(success_rates)}')
        # generate_agents(1)
        # attach_image_to_all_agents()
        # agents = FootballAgent.objects.all()
        # for agent in agents:
        #     agents_sell = get_agent_sold_players(agent)
        #     sum_get = get_agent_total_transfer_income(agent)
        #     print(f'Agent: {agent.first_name} {agent.last_name} - agent sell: {agents_sell['count']}, Sum: {sum_get}')
        # set_manual_day_today('2025-01-30')
        # finalize_euro_cup(current_euro_season, match)

        # season = get_current_season()
        # TeamState.process_all_teams(season)