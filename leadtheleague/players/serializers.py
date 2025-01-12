from rest_framework import serializers
from .models import Player

class PlayerSerializer(serializers.ModelSerializer):
    nationality = serializers.CharField(source='nationality.name', default="-")
    nationalityabbr = serializers.CharField(source='nationality.abbreviation', default="-")
    position = serializers.CharField(source='position.name', default="-")
    positionabbr = serializers.CharField(source='position.abbreviation', default="-")
    agent = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            'id', 'name', 'age', 'nationality', 'nationalityabbr',
            'position', 'positionabbr', 'agent', 'price', 'potential_rating', 'is_free_agent'
        ]

    def get_agent(self, obj):
        if obj.agent:
            return f"{obj.agent.first_name} {obj.agent.last_name}"
        return "No Agent"
