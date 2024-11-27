from django import forms


class TransferFilterForm(forms.Form):
    age = forms.IntegerField(
        required=False,
        label='Age',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter age'})
    )
    nationality = forms.ChoiceField(
        required=False,
        label='Nationality',
        choices=[],
    )
    position = forms.ChoiceField(
        required=False,
        label='Position',
        choices=[],
    )
    sort = forms.ChoiceField(
        required=False,
        label='Sort By',
        choices=[
            ('name', 'Name'),
            ('age', 'Age'),
            ('position', 'Position'),
        ]
    )
    order = forms.ChoiceField(
        required=False,
        label='Order',
        choices=[
            ('asc', 'Ascending'),
            ('desc', 'Descending'),
        ]
    )

    def __init__(self, *args, **kwargs):
        # Добавяне на динамични опции за nationality и position
        nationalities = kwargs.pop('nationalities', [])
        positions = kwargs.pop('positions', [])
        super().__init__(*args, **kwargs)
        self.fields['nationality'].choices = [('', 'All Nationalities')] + [(n, n) for n in nationalities]
        self.fields['position'].choices = [('', 'All Positions')] + [(p, p) for p in positions]
