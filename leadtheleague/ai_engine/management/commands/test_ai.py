from django.core.management import BaseCommand

from ai_engine.models import QTable
from teams.ai.state import TeamState


class Command(BaseCommand):
    help = "Тества AI логиката"

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Започва тестването на AI...")

        for _ in range(100):
            TeamState.process_all_teams(season=1)

        learned_data = list(QTable.objects.all().values())
        if not learned_data:
            self.stdout.write("⚠ AI не е записал нищо в QTable!")
        else:
            self.stdout.write(f"✅ AI е записал {len(learned_data)} записа в QTable.")
            for record in learned_data[:10]:  # Показваме първите 10 резултата
                self.stdout.write(str(record))

        self.stdout.write("🎯 Тестването приключи.")
