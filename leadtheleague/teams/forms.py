from django import forms
from .models import Team

class TeamCreationForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'abbr', 'color']

    COLOR_CHOICES = [
        ('red', 'Red'),
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('black', 'Black'),
        ('white', 'White'),
    ]

    color = forms.ChoiceField(choices=COLOR_CHOICES)
