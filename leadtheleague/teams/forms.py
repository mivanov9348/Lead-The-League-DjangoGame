from django import forms
from django.core.exceptions import ValidationError

from teams.models import Team


class TeamCreationForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'abbreviation']

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        abbreviation = cleaned_data.get('abbreviation')

        # Debugging output
        print("Cleaned data:", cleaned_data)

        if not name:
            raise ValidationError("Team Name is required!")
        if not abbreviation:
            raise ValidationError("Abbreviation must be 2-3 characters!")

        return cleaned_data


class TeamLogoForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['logo']
