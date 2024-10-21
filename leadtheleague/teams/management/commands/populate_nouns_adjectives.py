import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from teams.models import AdjectiveTeamNames, NounTeamNames

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        json_file_path = os.path.join(settings.BASE_DIR, 'teams', 'data', 'adj_nouns.json')

        with open(json_file_path) as f:
            data = json.load(f)

        adjectives = data.get('adjectives', [])
        nouns = data.get('nouns', [])

        for adj in adjectives:
            AdjectiveTeamNames.objects.get_or_create(word=adj)

        for noun in nouns:
            NounTeamNames.objects.get_or_create(word=noun)

        self.stdout.write(self.style.SUCCESS('Successfully Added!'))