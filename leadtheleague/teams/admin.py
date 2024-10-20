from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Team

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbr', 'color')  # Fields to display in the admin list view
    search_fields = ('name', 'abbr')  # Fields to enable search
