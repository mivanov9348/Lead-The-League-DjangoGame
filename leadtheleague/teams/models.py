from tkinter.constants import CASCADE
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db import models
from accounts.models import CustomUser
from game.models import Season
from leagues.models import League, Division

class AdjectiveTeamNames(models.Model):
    word = models.CharField(max_length=50)

    def __str__(self):
        return self.word

class NounTeamNames(models.Model):
    word = models.CharField(max_length=50)

    def __str__(self):
        return self.word

class Team(models.Model):
    name = models.CharField(max_length=100)
    abbr = models.CharField(max_length=3, validators=[MinLengthValidator(3), MaxLengthValidator(3)])
    color = models.CharField(max_length=20)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='team', null=True, blank=True)
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='team', null=True)
    is_dummy = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class TeamSeasonStats(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    league = models.ForeignKey(League, on_delete=models.CASCADE, null=True)
    division = models.ForeignKey(Division, on_delete=models.CASCADE, null=True)
    matches = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    goalscored = models.IntegerField(default=0)
    goalconceded = models.IntegerField(default=0)
    goaldifference = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    class Meta:
        unique_together = ('season', 'team')

class Tactics(models.Model):
    name = models.CharField(max_length=30)
    num_goalkeepers = models.IntegerField(default=1)
    num_defenders = models.IntegerField()
    num_midfielders = models.IntegerField()
    num_forwards = models.IntegerField()

    def __str__(self):
        return f'{self.name}'

class TeamTactics(models.Model):
    team = models.OneToOneField(Team, on_delete=models.CASCADE)
    tactic = models.ForeignKey(Tactics, on_delete=models.SET_NULL, null=True)
    starting_players = models.ManyToManyField('players.Player')

    def __str__(self):
        return f"{self.team.name} - {self.tactic.name}"
