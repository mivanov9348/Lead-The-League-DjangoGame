from django.contrib import admin, messages
from .models import Team, DummyTeamNames
from .utils import fill_dummy_teams

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbr', 'color')  # Fields to display in the admin list view
    search_fields = ('name', 'abbr')  # Fields to enable search
    actions = ['fill_with_dummy_teams']  # Register the action to fill divisions with dummy teams

    def fill_with_dummy_teams(self, request, queryset):
        fill_dummy_teams()  # Call the utility function to create dummy teams
        self.message_user(request, "Dummy teams created and divisions filled.", level=messages.SUCCESS)

    fill_with_dummy_teams.short_description = "Create Dummy Teams to Fill Divisions"  # Set a descriptive label

@admin.register(DummyTeamNames)
class AdjectiveTeamNamesAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbr')  # Adjust this if your model has other fields
    search_fields = ('name', 'abbr')  # Enable searching by the adjective word
