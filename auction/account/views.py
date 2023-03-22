from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages as dj_messages
from . import forms, models

POST = 'POST'


class Messages:
    """ Hints to user on profile edit page."""
    EDIT_SUCCESS = 'Profile updated successfully'
    EDIT_ERROR = 'Error updating your profile'


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """ User account management: edit account, change password."""
    DASHBOARD = 'account/dashboard.html'
    MENU_SECTION = 'dashboard'

    return render(request, DASHBOARD, {'section': MENU_SECTION})


def register(request: HttpRequest) -> HttpResponse:
    """ Register new user."""
    REGISTER = 'account/register.html'
    REGISTER_DONE = 'account/register_done.html'

    if request.method == POST:
        user_form = forms.UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password1'])
            new_user.save()
            models.Profile.objects.create(user=new_user)
            return render(request, REGISTER_DONE, {'new_user': new_user})
    else:
        user_form = forms.UserRegistrationForm()

    return render(request, REGISTER, {'user_form': user_form})


@login_required
def edit(request: HttpRequest) -> HttpResponse:
    """ Edit user account."""
    EDIT = 'account/edit.html'

    # create profile object if it doesn't exist because admins may not have profile
    if not getattr(request.user, 'profile', None):
        profile = models.Profile.objects.create(user=request.user)
    else:
        profile = request.user.profile

    if request.method == POST:
        user_form = forms.UserEditForm(instance=request.user, data=request.POST)
        profile_form = forms.ProfileEditForm(
            instance=profile,
            data=request.POST,
            files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            dj_messages.success(request, Messages.EDIT_SUCCESS)
        else:
            dj_messages.error(request, Messages.EDIT_ERROR)
    else:
        user_form = forms.UserEditForm(instance=request.user)
        profile_form = forms.ProfileEditForm(instance=profile)

    return render(request, EDIT, {'user_form': user_form, 'profile_form': profile_form})
