from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect

from django.contrib import messages

from .forms import Room_Name
from .consumers import generate_room_name, RoomConsumer

import requests
import json
import asyncio

import random


def index(request):
    return redirect('/join')

def join(request):
    data = {'twitch_login': request.session.get('twitch_login')}
    return render(request, 'main/join.html', data)

def create(request):
    data = {'twitch_login': request.session.get('twitch_login')}
    return render(request, 'main/create.html', data)


def host(request):
    if request.session.get('twitch_login') is None:
        return redirect('/join')

    room_name = generate_room_name()
    return render(request, 'main/host.html', {'room_name': room_name, 'twitch_login': request.session.get('twitch_login', '')})


def room(request):
    if request.session.get('twitch_login') is None:
        return redirect('/join')

    if request.method == 'POST':
        room_name = request.POST.get('room_name', '')

        if room_name in RoomConsumer.rooms:
            return render(request, 'main/room.html', {'room_name': room_name, 'twitch_login': request.session.get('twitch_login', '')})

    return redirect('/join')


def login(request):
    if request.method == 'POST':
        access_token = request.POST.get('access_token', '')
        try:
            client_id = 'f88v1abv16wh89ssce0hhvoswqvl9o'
            URL = 'https://api.twitch.tv/helix/users'
            API_HEADERS = {
                'Client-ID': client_id,
                'Authorization': 'Bearer ' + access_token,
            }
            res = requests.get(URL, headers=API_HEADERS)
            res.raise_for_status()
            request.session['access_token'] = access_token
            request.session['twitch_login'] = res.json()['data'][0]['login']
        except:
            request.session['access_token'] = None
            request.session['twitch_login'] = None

        return redirect('/join')

    return render(request, 'main/login.html')
