from django.core.validators import MinValueValidator, MaxValueValidator
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

# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=100)
    abbr = models.CharField(max_length=3, validators=[MinValueValidator(3), MaxValueValidator(3)])
    color = models.CharField(max_length=20)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='team', null=True, blank = True)
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