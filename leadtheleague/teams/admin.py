from django.contrib import admin
from .models import Team, AdjectiveTeamNames, NounTeamNames

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbr', 'color')  # Fields to display in the admin list view
    search_fields = ('name', 'abbr')  # Fields to enable search

@admin.register(AdjectiveTeamNames)
class AdjectiveTeamNamesAdmin(admin.ModelAdmin):
    list_display = ('word',)  # Adjust this if your model has other fields
    search_fields = ('word',)  # Enable searching by the adjective word

@admin.register(NounTeamNames)
class NounTeamNamesAdmin(admin.ModelAdmin):
    list_display = ('word',)  # Adjust this if your model has other fields
    search_fields = ('word',)  # Enable searching by the noun word
