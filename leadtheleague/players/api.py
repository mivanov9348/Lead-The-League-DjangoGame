from rest_framework.decorators import api_view

from players.models import Player
from players.pagination import PlayerPagination
from players.serializers import PlayerSerializer


@api_view(['GET'])
def players_list_api(request):
    """API за връщане на играчи с пагинация."""
    players = Player.objects.select_related('nationality', 'position', 'agent').all()
    paginator = PlayerPagination()
    paginated_players = paginator.paginate_queryset(players, request)
    serializer = PlayerSerializer(paginated_players, many=True)
    return paginator.get_paginated_response(serializer.data)
