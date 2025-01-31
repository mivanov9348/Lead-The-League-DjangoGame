import random
from django.db import transaction
from django.db.models import Q, F
from match.models import MatchEvent
from match.utils.match.attendance import calculate_match_attendance, calculate_match_income
from match.utils.match.goalscorers import log_goalscorer
from match.utils.match.retrieval import get_opposing_team
from players.models import PlayerMatchStatistic
from teams.models import TeamTactics, TeamPlayer


def choose_event_random_player(team):
    try:
        team_tactics = TeamTactics.objects.select_related('team').get(team=team)

        starting_player = team_tactics.starting_players.exclude(position__name='Goalkeeper').order_by('?').first()

        return starting_player
    except TeamTactics.DoesNotExist:
        return None


def update_match_minute(match):
    increment = random.randint(1, 7)
    match.current_minute = min(match.current_minute + increment, 90)
    return match.current_minute


def get_match_team_initiative(match):
    return match.home_team if match.is_home_initiative else match.away_team


def finalize_match(match):
    with transaction.atomic():
        match.is_played = True

        if hasattr(match, 'penalties') and match.penalties.is_completed:
            penalties = match.penalties
            print(f"Match went to penalties: Home {penalties.home_score} - Away {penalties.away_score}")

            if penalties.home_score > penalties.away_score:
                match.winner = match.home_team
            elif penalties.away_score > penalties.home_score:
                match.winner = match.away_team
            else:
                raise ValueError("Invalid state: Penalties completed but no winner determined.")
        else:
            if match.home_goals > match.away_goals:
                match.winner = match.home_team
            elif match.away_goals > match.home_goals:
                match.winner = match.away_team
            else:
                match.winner = None

        print(f'Tuk li greshis mama ti prosta?')
        calculate_match_attendance(match)
        print(f'Tuk li greshis mama ti prosta? 2')
        calculate_match_income(match, match.home_team)
        print(f'Tuk li greshis mama ti prosta? 3')
        match.save()

        fixture = match.fixture
        if not fixture:
            raise ValueError("Match has no fixture.")

        fixture.home_goals = match.home_goals
        fixture.away_goals = match.away_goals
        fixture.is_finished = True

        fixture.winner = match.winner
        fixture.save()

    print(f"Match finalized: {match}. Fixture updated.")


def update_player_stats_from_template(match, event_result, player):
    if not player:
        print("No player provided for statistics update.")
        return
    event_fields_to_stats = {
        "goals": "Goals",
        "assists": "Assists",
        "shoots": "Shoots",
        "shootsOnTarget": "ShootsOnTarget",
        "saves": "Saves",
        "passes": "Passes",
        "tackles": "Tackles",
        "fouls": "Fouls",
        "dribbles": "Dribbles",
        "yellowCards": "YellowCards",
        "redCards": "RedCards",
        "conceded": "Conceded",
    }
    # Зареждаме или създаваме статистика за играча
    player_stat, created = PlayerMatchStatistic.objects.get_or_create(
        player=player,
        match=match,
        defaults={"statistics": {stat: 0 for stat in event_fields_to_stats.values()}},
    )
    updated_stats = player_stat.statistics
    # Обновяване на статистиките на играча
    for field, stat_name in event_fields_to_stats.items():
        stat_value = getattr(event_result, field, 0)
        if stat_value > 0:
            updated_stats[stat_name] = updated_stats.get(stat_name, 0) + stat_value
    # Оптимизирано: Зареждаме само необходимите данни за вратаря на противниковия отбор
    player_team = TeamPlayer.objects.select_related("team").filter(player=player).first()
    opposing_team = get_opposing_team(match, player_team.team)
    opposing_goalkeeper = (
        opposing_team.teamtactics.starting_players.filter(position__name="Goalkeeper").only("id").first()
    )
    if event_result.event_result in {"ShotOnTarget", "Goal"} and opposing_goalkeeper:
        gk_stat, _ = PlayerMatchStatistic.objects.get_or_create(
            player=opposing_goalkeeper,
            match=match,
            defaults={"statistics": {stat: 0 for stat in event_fields_to_stats.values()}},
        )
        gk_stats = gk_stat.statistics
        if event_result.event_result == "ShotOnTarget":
            gk_stats["Saves"] = gk_stats.get("Saves", 0) + 1
        elif event_result.event_result == "Goal":
            gk_stats["Conceded"] = gk_stats.get("Conceded", 0) + 1
        gk_stat.statistics = gk_stats
        gk_stat.save()
    # Оптимизирано: Актуализираме случайно съотборник само ако е нужно
    if event_result.event_result == "Goal":
        teammates = player.team.teamtactics.starting_players.exclude(id=player.id).only("id")
        if teammates.exists():
            random_teammate = random.choice(list(teammates))
            teammate_stat, _ = PlayerMatchStatistic.objects.get_or_create(
                player=random_teammate,
                match=match,
                defaults={"statistics": {stat: 0 for stat in event_fields_to_stats.values()}},
            )
            teammate_stats = teammate_stat.statistics
            teammate_stats["Assists"] = teammate_stats.get("Assists", 0) + 1
            teammate_stat.statistics = teammate_stats
            teammate_stat.save()
    if not created:
        player_stat.statistics = updated_stats
        player_stat.save()

def update_match_score(event_result, match, team_with_initiative, player):
    goal_events = {"ShotGoal", "CornerGoal", "FreeKickGoal", "PenaltyGoal"}

    if event_result.event_result in goal_events:
        log_goalscorer(match, player, team_with_initiative)

        if team_with_initiative == match.home_team:
            match.home_goals = F("home_goals") + 1
        else:
            match.away_goals = F("away_goals") + 1

        match.save(update_fields=["home_goals", "away_goals"])

        match.refresh_from_db(fields=["home_goals", "away_goals"])


def check_initiative(template, match):
    if not template.event_result.possession_kept:
        match.is_home_initiative = not match.is_home_initiative

        match.save(update_fields=["is_home_initiative"])
    else:
        print("The initiative saved")


def fill_template_with_player(template, player):
    def get_team_name(player):
        team_player = player.team_players.first()
        return team_player.team.name if team_player else "No Team"

    player_name = f"{player.first_name} {player.last_name} ({get_team_name(player)})"

    formatted_text = template.template_text.format(player_1=player_name)
    return formatted_text


def handle_card_event(event_result, player, match, team):
    current_minute = match.current_minute
    print(f"Handling card event: {event_result.event_result} at minute {current_minute}")

    try:
        player_match_stat, created = PlayerMatchStatistic.objects.get_or_create(
            player=player,
            match=match
        )
        print(f"PlayerMatchStatistic {'created' if created else 'retrieved'} for player {player.name}")

        statistics = player_match_stat.statistics or {}
        print(f"Initial statistics: {statistics}")

        if event_result.event_result == "RedCard":
            print(f"Red card issued to player {player.name}")
            player.has_red_card = True
            remove_player_from_team(player, team)
            log_card_event(match, current_minute, "Red Card", player)

            statistics["RedCards"] = statistics.get("RedCards", 0) + 1
            print(f"Updated red card count: {statistics['RedCards']}")

        elif event_result.event_result == "YellowCard":
            print(f"Yellow card issued to player {player.name}")
            player.yellow_cards += 1
            log_card_event(match, current_minute, "Yellow Card", player)

            statistics["YellowCards"] = statistics.get("YellowCards", 0) + 1
            print(f"Updated yellow card count: {statistics['YellowCards']}")

            if player.yellow_cards >= 2:
                print(f"Player {player.name} has 2 yellow cards, issuing red card")
                player.has_red_card = True
                remove_player_from_team(player, team)
                log_card_event(match, current_minute, "Red Card", player)

                statistics["RedCards"] = statistics.get("RedCards", 0) + 1
                print(f"Updated red card count due to 2 yellows: {statistics['RedCards']}")

        player_match_stat.statistics = statistics
        player_match_stat.save()
        print(f"PlayerMatchStatistic saved for player {player.name}")

        player.save()
        print(f"Player {player.name} updated and saved")

    except Exception as e:
        print(f"Error handling card event: {e}")


def remove_player_from_team(player, team):
    try:
        team_tactics = TeamTactics.objects.select_related('team').get(team=team)
        starting_players = team_tactics.starting_players

        if starting_players.filter(pk=player.pk).exists():
            starting_players.remove(player)
            team_tactics.save()
    except TeamTactics.DoesNotExist:
        print(f"Team tactics not found for team {team.name}.")
    except Exception as e:
        print(f"Unexpected error removing player {player.first_name} {player.last_name} from team {team.name}: {e}")


def log_card_event(match, minute, card_type, player):
    if card_type not in ["Yellow Card", "Red Card"]:
        raise ValueError("Invalid card type. Must be 'Yellow Card' or 'Red Card'.")

    try:
        with transaction.atomic():
            description = f"{card_type} for {player.name} in the {minute}' minute."

            match_event_data = {
                "match": match,
                "minute": minute,
                "event_type": card_type,
                "description": description,
                "is_negative_event": True,
                "possession_kept": False,
            }

            match_event = MatchEvent.objects.create(**match_event_data)
            match_event.players.add(player)

            print(f"{card_type} logged for {player.name} in match {match.id} at minute {minute}.")
    except Exception as e:
        print(f"Error logging {card_type} for {player.name}: {e}")


def log_match_participate(match):
    try:
        home_team_tactics = TeamTactics.objects.select_related('team').prefetch_related('starting_players').get(
            team=match.home_team
        )
        print(f"Loaded home_team_tactics: {home_team_tactics}")

        away_team_tactics = TeamTactics.objects.select_related('team').prefetch_related('starting_players').get(
            team=match.away_team
        )
        print(f"Loaded away_team_tactics: {away_team_tactics}")

    except TeamTactics.DoesNotExist as e:
        print(f"Error: TeamTactics not found for one of the teams in match {match}. Details: {e}")
        return  # Спиране на изпълнението, ако няма тактика за някой от отборите

    all_players = list(home_team_tactics.starting_players.all()) + list(away_team_tactics.starting_players.all())
    print(f"All players for match: {[player.id for player in all_players]}")

    if not all_players:
        print(f"No players found for match {match}.")
        return  # Спиране, ако няма играчи

    existing_stats = PlayerMatchStatistic.objects.filter(
        Q(match=match) & Q(player__in=all_players)
    ).select_related('player')

    if not existing_stats.exists():
        print(f"No existing statistics found for match {match}. Creating new ones.")
    else:
        print(f'Existing stats count: {existing_stats.count()}')

    existing_players = {stat.player_id for stat in existing_stats}
    print(f'Existing player IDs: {existing_players}')

    new_players = [player for player in all_players if player.id not in existing_players]
    print(f"New players for statistics: {[player.id for player in new_players]}")

    new_stats = [
        PlayerMatchStatistic(
            player=player,
            match=match,
            statistics={"Matches": 1}
        )
        for player in new_players
    ]

    if new_stats:
        PlayerMatchStatistic.objects.bulk_create(new_stats)
    else:
        print("No new statistics to create.")

    with transaction.atomic():
        for stat in existing_stats:
            try:
                print(f"Processing existing stat for Player ID={stat.player.id}, Match ID={stat.match.id}")
                if stat.statistics.get("Matches", 0) == 0:
                    print(f"Updating 'Matches' field from 0 to 1 for Player ID={stat.player.id}")
                    stat.statistics["Matches"] = 1
                    stat.save()
                    print(f"Statistics updated: {stat.statistics}")
                else:
                    print(
                        f"'Matches' field is already updated for Player ID={stat.player.id}, value={stat.statistics['Matches']}")
            except Exception as e:
                print(f"Error updating statistics for Player ID={stat.player.id}. Details: {e}")


def log_clean_sheets(match):
    try:
        home_team_tactics = TeamTactics.objects.select_related('team').prefetch_related('starting_players').get(
            team=match.home_team
        )
        print(f"Loaded home_team_tactics: {home_team_tactics}")

        away_team_tactics = TeamTactics.objects.select_related('team').prefetch_related('starting_players').get(
            team=match.away_team
        )
        print(f"Loaded away_team_tactics: {away_team_tactics}")

    except TeamTactics.DoesNotExist as e:
        print(f"Error: TeamTactics not found for one of the teams in match {match}. Details: {e}")
        return  # Stop execution if no tactics found for a team

    # Check if either team conceded goals
    home_team_goals_conceded = match.away_goals > 0
    away_team_goals_conceded = match.home_goals > 0

    print(f"Goals conceded: Home Team={home_team_goals_conceded}, Away Team={away_team_goals_conceded}")

    goalkeepers = {}

    try:
        home_goalkeeper = home_team_tactics.starting_players.filter(position__name="Goalkeeper").first()
        away_goalkeeper = away_team_tactics.starting_players.filter(position__name="Goalkeeper").first()

        if home_goalkeeper:
            goalkeepers[home_goalkeeper.id] = home_goalkeeper
        if away_goalkeeper:
            goalkeepers[away_goalkeeper.id] = away_goalkeeper

        print(f"Identified goalkeepers: {goalkeepers}")

    except Exception as e:
        print(f"Error retrieving goalkeepers. Details: {e}")
        return

    with transaction.atomic():
        # Update or create CleanSheets for home goalkeeper
        if not home_team_goals_conceded and home_goalkeeper:
            stat, created = PlayerMatchStatistic.objects.get_or_create(
                player=home_goalkeeper,
                match=match,
                defaults={"statistics": {"CleanSheets": 1}},
            )

            if not created:
                clean_sheets = stat.statistics.get("CleanSheets", 0)
                stat.statistics["CleanSheets"] = clean_sheets + 1
                stat.save()
                print(f"Updated CleanSheets for Home Goalkeeper ID={home_goalkeeper.id}: {stat.statistics}")
            else:
                print(
                    f"Created new CleanSheets statistic for Home Goalkeeper ID={home_goalkeeper.id}: {stat.statistics}")

        # Update or create CleanSheets for away goalkeeper
        if not away_team_goals_conceded and away_goalkeeper:
            stat, created = PlayerMatchStatistic.objects.get_or_create(
                player=away_goalkeeper,
                match=match,
                defaults={"statistics": {"CleanSheets": 1}},
            )

            if not created:
                clean_sheets = stat.statistics.get("CleanSheets", 0)
                stat.statistics["CleanSheets"] = clean_sheets + 1
                stat.save()
                print(f"Updated CleanSheets for Away Goalkeeper ID={away_goalkeeper.id}: {stat.statistics}")
            else:
                print(
                    f"Created new CleanSheets statistic for Away Goalkeeper ID={away_goalkeeper.id}: {stat.statistics}")

    print("CleanSheets logging completed.")
