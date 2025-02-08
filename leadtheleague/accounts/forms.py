from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    avatar = forms.CharField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'avatar')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("This field cannot be null.")
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError('A user with this username already exists.')
        return username

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if not avatar:
            self.add_error('avatar', 'You must select an avatar.')
        return avatar

