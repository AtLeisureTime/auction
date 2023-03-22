from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """ Home page with auction rules and news."""
    INDEX = 'index.html'
    MENU_SECTION = 'home'

    return render(request, INDEX, {'section': MENU_SECTION})
