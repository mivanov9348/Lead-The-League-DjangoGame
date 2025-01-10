from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from accounts.models import CustomUser
from django.db.models import JSONField


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    abbreviation = models.CharField(max_length=3)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='team', null=True, blank=True)
    reputation = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10000)], null=True, blank=True)
    is_COM = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    nationality = models.ForeignKey('core.Nationality', on_delete=models.SET_NULL, related_name='nation_teams',
                                    null=True,
                                    blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TeamFinance(models.Model):
    team = models.OneToOneField(Team, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f'{self.team.name} Balance: {self.balance}'


class TeamTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'Income'),
        ('OUT', 'Expense'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team_transactions')
    bank = models.ForeignKey("finance.Bank", on_delete=models.CASCADE, related_name='team_transactions')
    season = models.ForeignKey('game.Season', on_delete=models.SET_NULL, related_name='team_transactions', null=True,
                               blank=True)
    type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.amount} ({self.team.name})"


class TeamPlayer(models.Model):
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE, related_name='team_players')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team_players')
    shirt_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)], null=True, blank=True)

    class Meta:
        unique_together = ('team', 'shirt_number')

    def __str__(self):
        return f"{self.player.name} - {self.team.name} (# {self.shirt_number})"


class TeamStatistic(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class TeamMatchStatistic(models.Model):
    team = models.ForeignKey(Team, related_name='match_stats', on_delete=models.CASCADE)
    match = models.ForeignKey('match.Match', on_delete=models.CASCADE)
    statistic = models.ForeignKey(TeamStatistic, on_delete=models.CASCADE)
    player = models.ForeignKey('players.Player', related_name='goalscorers', on_delete=models.CASCADE, null=True,
                               blank=True)
    value = models.FloatField(default=0)

    class Meta:
        unique_together = ('team', 'match', 'statistic', 'player')
        indexes = [
            models.Index(fields=['team']),
            models.Index(fields=['match']),
            models.Index(fields=['statistic']),
            models.Index(fields=['player']),
        ]


class Tactics(models.Model):
    name = models.CharField(max_length=30, unique=True)
    num_goalkeepers = models.IntegerField(default=1)
    num_defenders = models.IntegerField()
    num_midfielders = models.IntegerField()
    num_attackers = models.IntegerField()

    def __str__(self):
        return f'{self.name}'


class TeamTactics(models.Model):
    team = models.OneToOneField(Team, on_delete=models.CASCADE)
    tactic = models.ForeignKey(Tactics, on_delete=models.SET_NULL, null=True)
    starting_players = models.ManyToManyField(
        'players.Player',
        related_name='starting_team_tactics'
    )
    reserve_players = models.ManyToManyField(
        'players.Player',
        related_name='reserve_team_tactics'
    )

    def __str__(self):
        return f"{self.team.name} - {self.tactic.name}"

    class Meta:
        indexes = [
            models.Index(fields=['team']),
            models.Index(fields=['tactic']),
        ]


class TrainingImpact(models.Model):
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE, related_name='trainings')
    coach = models.ForeignKey('staff.Coach', on_delete=models.CASCADE, related_name='trainings')
    date = models.DateTimeField(auto_now_add=True)
    training_impact = models.DecimalField(max_digits=4, decimal_places=2)
    notes = models.TextField(null=True, blank=True)


class TeamSeasonAnalytics(models.Model):
    team = models.ForeignKey(Team, related_name='season_analytics', on_delete=models.CASCADE)
    season = models.ForeignKey('game.Season', on_delete=models.CASCADE)
    league_season = models.ForeignKey(
        'leagues.LeagueSeason',
        related_name="league_teams",
        on_delete=models.CASCADE,
        null=True
    )
    matches = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    goalscored = models.PositiveIntegerField(default=0)
    goalconceded = models.PositiveIntegerField(default=0)
    points = models.FloatField(default=0.0)

    def calculate_average(self):
        self.average_points = self.points / self.matches if self.matches > 0 else 0
        self.save()
