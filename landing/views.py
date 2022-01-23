import mimetypes
import requests

from django.shortcuts import render
from django.conf import settings


def index(request):
    return render(request, 'base_landing.html')


def petitions(request):
    return render(request, 'petitions.html')
