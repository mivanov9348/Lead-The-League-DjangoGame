from django.db.models import Prefetch

from messaging.utils.category_messages_utils import create_free_agent_transfer_message
from staff.utils.agent_utils import agent_sell_player
from teams.models import TeamPlayer
from transfers.models import Transfer, TransferOffer


def get_all_transfers():
    return Transfer.objects.all()


def transfer_history_by_team(team_id):
    transfers_in = Transfer.objects.filter(buying_team_id=team_id).order_by('-transfer_date')
    transfers_out = Transfer.objects.filter(selling_team_id=team_id).order_by('-transfer_date')

    transfers = {
        'transfers_in': transfers_in,
        'transfers_out': transfers_out,
    }
    return transfers


def create_transfer(team, player, is_free_agent):
    Transfer.objects.create(
        player=player,
        buying_team=team,
        selling_team=None if is_free_agent else player.team,
        amount=player.price,
        is_free_agent=is_free_agent
    )


def transfer_free_agent(team, player):
    agent_sell_player(team, player)
    create_transfer(team, player, True)
    create_free_agent_transfer_message(player, team)

def find_transfer_offer_by_id(offer_id):
    try:
        return TransferOffer.objects.select_related('offering_team').prefetch_related(
            Prefetch('player__team_players', queryset=TeamPlayer.objects.select_related('teams'))
        ).get(id=offer_id)
    except TransferOffer.DoesNotExist:
        return None


def create_transfer_record(player_team, offering_team, player, amount):
    return Transfer.objects.create(
        selling_team=player_team,
        buying_team=offering_team,
        player=player,
        amount=amount
    )
