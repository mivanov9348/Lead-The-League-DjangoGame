from wsgiref.validate import validator

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

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

    # players = models.ManyToManyField('Player', blank = True)

    def __str__(self):
        return self.name