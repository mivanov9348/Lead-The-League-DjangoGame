import random
from datetime import date
from decimal import Decimal
from django.db.models import Prefetch
from game.models import MatchSchedule
from game.utils.get_season_stats_utils import get_current_season
from messaging.utils.category_messages_utils import create_team_to_team_transfer_message
from teams.models import TeamPlayer
from teams.utils.team_finance_utils import sell_player_income, buy_player_expense
from teams.utils.update_team_stats import get_available_shirt_number
from transfers.models import Transfer, TransferOffer


def is_transfer_day():
    current_season = get_current_season()
    current_date = current_season.current_date
    return MatchSchedule.objects.filter(date=current_date, event_type='transfer').exists()


def get_all_transfers():
    return Transfer.objects.all()


from transfers.models import Transfer


def get_latest_transfers(limit=5):
    return Transfer.objects.select_related('player', 'selling_team', 'buying_team') \
               .order_by('-transfer_date')[:limit]


def transfer_history_by_team(team_id):
    transfers_in = Transfer.objects.filter(buying_team_id=team_id).order_by('-transfer_date')
    transfers_out = Transfer.objects.filter(selling_team_id=team_id).order_by('-transfer_date')

    transfers = {
        'transfers_in': transfers_in,
        'transfers_out': transfers_out,
    }
    return transfers


def create_transfer(team, player, is_free_agent):
    season = get_current_season()
    selling_team = None
    if not is_free_agent:
        current_team_player = player.team_players.first()
        selling_team = current_team_player.team if current_team_player else None

    Transfer.objects.create(
        season=season,
        player=player,
        buying_team=team,
        selling_team=selling_team,
        amount=player.price,
        is_free_agent=is_free_agent
    )


def find_transfer_offer_by_id(offer_id):
    try:
        return TransferOffer.objects.select_related('offering_team').prefetch_related(
            Prefetch('player__team_players', queryset=TeamPlayer.objects.select_related('teams'))
        ).get(id=offer_id)
    except TransferOffer.DoesNotExist:
        return None


def COM_receive_transfer_offer(transfer_offer):
    team_player = transfer_offer.player.team_players.first()
    player_team = team_player.team if team_player else None
    current_season = get_current_season()

    if not player_team or player_team.user is not None:
        return False, "Offer decision skipped (team is controlled by a user)."

    try:
        player_price = Decimal(transfer_offer.player.price)
        offer_amount = Decimal(transfer_offer.offer_amount)
    except (ValueError, TypeError) as e:
        return False, f"Invalid data: {e}"

    acceptable_lower_bound = player_price * Decimal("0.9")
    acceptable_upper_bound = player_price

    random_factor = Decimal(random.uniform(0.85, 1.05))
    final_decision_threshold = player_price * random_factor

    if acceptable_lower_bound <= offer_amount <= final_decision_threshold or offer_amount > player_price:
        transfer_offer.status = 'Accepted'
        transfer_offer.save()

        team_player = transfer_offer.player.team_players.first()
        offering_team = transfer_offer.offering_team
        amount = offer_amount

        # Намираме минималния свободен номер
        shirt_number = get_available_shirt_number(offering_team)
        team_player.shirt_number = shirt_number

        sell_player_income(player_team, transfer_offer.player, amount)
        buy_player_expense(offering_team, transfer_offer.player, amount)

        Transfer.objects.create(
            season=current_season,
            selling_team=player_team,
            buying_team=offering_team,
            player=transfer_offer.player,
            amount=amount
        )

        team_player.team = offering_team
        team_player.save()

        create_team_to_team_transfer_message(transfer_offer.player, player_team, offering_team, amount)

        return True, f"Offer accepted by AI team. Player transferred with new shirt number {shirt_number}."
    else:
        transfer_offer.status = 'Rejected'
        transfer_offer.save()
        return False, "Offer rejected by AI team."
