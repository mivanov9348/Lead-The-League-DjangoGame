from django.utils import timezone
from django.shortcuts import get_object_or_404
from huey.contrib.djhuey import periodic_task, task
from huey import crontab
from fixtures.utils import match_to_fixture
from teams.utils import update_team_stats
from .models import Match, EventTemplate
from .utils import log_match_event, finalize_match
from .views import next_event

@periodic_task(crontab(minute='17', hour='17'))
def start_matches():
    print("start_matches task triggered")
    today = timezone.now().date()
    matches_today = Match.objects.filter(match_date=today)
    print(f"Found {matches_today.count()} matches for today.")

    for match in matches_today:
        print(f"Starting events for match {match.id}...")
        set_kick_off(match.id)  # Start with kickoff for each match

@task()
def set_kick_off(match_id):
    match = get_object_or_404(Match, id=match_id)
    kickoff_template = EventTemplate.objects.filter(event_result="Kick Off").first()

    if kickoff_template:
        log_match_event(
            match=match,
            minute=0,
            template=kickoff_template,
            formattedText=kickoff_template.template_text,
            players=None
        )
    print(f"Kickoff event logged for match {match.id}.")

    # Start the match events
    start_match_events(match.id, 0)

@task()
def start_match_events(match_id, current_second):
    match = get_object_or_404(Match, id=match_id)

    if match.current_minute >= 90 or match.is_played:
        print(f"Match {match.id} has reached Full-Time or is already marked as played.")
        set_full_time(match_id)  # Trigger Full-Time event
        return

    next_event(match_id)

    if match.current_minute < 90:
        print(f"Scheduling next event for match {match.id} in 5 seconds.")
        start_match_events.schedule((match.id, current_second + 5), delay=5)  # Re-schedule with delay


@task()
def set_full_time(match_id):
    match = get_object_or_404(Match, id=match_id)
    match.is_played = True
    match.save()

    # Използване на шаблон за Full-Time събитие
    full_time_template = EventTemplate.objects.filter(event_result="Full-Time").first()
    if full_time_template:
        try:
            # Важно: проверете правилните аргументи за log_match_event и променете при нужда
            log_match_event(
                match=match,
                minute=90,  # вместо current_minute, използваме minute
                template=full_time_template,
                formattedText=full_time_template.template_text,
                players=None
            )
            print(f"Full-Time event logged for match {match.id}.")
        except TypeError as e:
            print(f"Error logging Full-Time event for match {match.id}: {e}")
            # Можем да излезем от задачата, ако има грешка, без да спираме worker-ите
            return
    else:
        print(f"No Full-Time template found for match {match.id}.")

@periodic_task(crontab(minute='25', hour='17'))
def finalize_day_matches():
    today = timezone.now().date()
    if not Match.objects.filter(match_date=today, is_played=False).exists():
        print(f"All matches for {today} have finished. Finalizing statistics.")
        for match in Match.objects.filter(match_date=today, is_played=True):
            finalize_match(match)
            update_team_stats(match)
            match_to_fixture(match)
    else:
        print(f"There are still ongoing matches for {today}. Will check again later.")
