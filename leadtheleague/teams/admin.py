from django.contrib import admin, messages
from players.utils.generate_player_utils import generate_team_players
from .models import Team
from .utils.generate_team_utils import set_team_logos
from .utils.lineup_utils import auto_select_starting_lineup


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'user',)
    search_fields = ('name', 'abbreviation', 'user__username')

    def fill_selected_teams_with_players(self, request, queryset):
        successful_teams = 0
        for team in queryset:
            try:
                generate_team_players(team)
                successful_teams += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Error generating players for team {team.name}: {e}",
                    level=messages.ERROR
                )
        self.message_user(
            request,
            f"Players successfully generated for {successful_teams} teams(s).",
            level=messages.SUCCESS
        )

    def set_team_logos_action(self, request, queryset):
        successful_teams, errors = set_team_logos()
        if successful_teams > 0:
            self.message_user(
                request,
                f"Logos successfully set for {successful_teams} teams(s).",
                level=messages.SUCCESS
            )
        if errors:
            for error in errors:
                self.message_user(
                    request,
                    error,
                    level=messages.WARNING
                )

    def automatic_starting_lineup_action(self, request, queryset):
        """Automatically select starting lineup for the selected teams."""
        successful_teams = 0
        for team in queryset:
            try:
                errors = auto_select_starting_lineup(team)
                if errors:
                    self.message_user(
                        request,
                        f"Team {team.name}: " + ", ".join(errors),
                        level=messages.WARNING
                    )
                else:
                    successful_teams += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Error setting lineup for team {team.name}: {e}",
                    level=messages.ERROR
                )
        if successful_teams > 0:
            self.message_user(
                request,
                f"Automatic starting lineup successfully set for {successful_teams} team(s).",
                level=messages.SUCCESS
            )

    actions = [
        'fill_selected_teams_with_players',
        'set_team_logos_action',
        'automatic_starting_lineup_action',
    ]

    fill_selected_teams_with_players.short_description = "Fill Selected Teams with Players"
    set_team_logos_action.short_description = "Set Logos for Selected Teams"
    automatic_starting_lineup_action.short_description = "Automatic Starting Lineup for Selected Teams"
