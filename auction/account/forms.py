from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from . import models


class ValidatnErrors:
    """ Hints to user on forms of this module."""
    EMAIL_IN_USE = 'Email is already in use.'


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']  # TODO: maybe validate whether email is unique


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self) -> str:
        """ Validate there is no user with the same email."""
        cleaned_email = self.cleaned_data.get('email')
        qs = User.objects.exclude(id=self.instance.id).filter(email=cleaned_email)
        if qs.exists():
            raise forms.ValidationError(ValidatnErrors.EMAIL_IN_USE)
        return cleaned_email


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = models.Profile
        fields = ['date_of_birth', 'photo']
