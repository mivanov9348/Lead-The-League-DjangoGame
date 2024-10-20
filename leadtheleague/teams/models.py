from django.db import models

# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=100)
    abbr = models.CharField(max_length=3)
    color = models.CharField(max_length=20)

    # players = models.ManyToManyField('Player', blank = True)

    def __str__(self):
        return self.name