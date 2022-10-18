import json
import asyncio
from collections import deque

import random
import string
import itertools

from .game import Game

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from django.shortcuts import render, redirect


def generate_room_name():
    all = set([''.join(_) for _ in itertools.product(string.ascii_uppercase, repeat=4)])
    used = set(RoomConsumer.rooms.keys())
    new = random.choice(list(all - used))
    return new


class RoomConsumer(AsyncJsonWebsocketConsumer):
    rooms = {}
    user_room = {} # user_name - room_name

    def get_host_channel(self):
        return self.rooms[self.room_name]['host_channel']

    def get_user_list(self):
        return self.rooms[self.room_name]['user_list']

    def get_all_user(self):
        user_list = list(self.get_user_list().items())

        room = self.rooms[self.room_name]
        host_name = room['host_name']
        host_channel = room['host_channel']
        streamer_channel = room['streamer_channel']

        user_list += [(host_name, host_channel)]
        if streamer_channel is not None:
            user_list += [(host_name, streamer_channel)]

        return user_list


    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.user_name = str(await database_sync_to_async(self.scope['session'].get)('twitch_login'))

        # twitch authentification
        if self.user_name is None:
            await self.close()

        # user exist
        if self.user_name in self.user_room:
            # new room_name != old room_name
            old_room_name = self.user_room[self.user_name]
            if self.room_name != old_room_name:
                if self.user_name == self.rooms[old_room_name]['host_name']:
                    old_channel_name = self.rooms[old_room_name]['host_channel']
                else:
                    old_channel_name = self.rooms[old_room_name]['user_list'][self.user_name]
                await self.channel_layer.send(old_channel_name, {
                    'type': 'close_connect'
                })
            # user is host
            elif self.user_name == self.rooms[self.room_name]['host_name']:
                if self.rooms[self.room_name]['streamer_channel'] is not None:
                    await self.channel_layer.send(self.rooms[self.room_name]['streamer_channel'], {
                        'type': 'close_connect'
                    })
                self.rooms[self.room_name]['streamer_channel'] = self.channel_name
                await self.channel_layer.send(self.rooms[self.room_name]['host_channel'], {
                    'type': 'message',
                    'action': 'switch_streamer_mode',
                    'streamer_mode': True,
                })
            # user is not host
            else:
                user_list = self.rooms[self.room_name]['user_list']
                await self.channel_layer.send(user_list[self.user_name], {
                    'type': 'close_connect'
                })

        if self.room_name not in self.rooms:
            self.rooms[self.room_name] = {
                'game': Game(self.room_name),
                'host_name': self.user_name,
                'host_channel': self.channel_name,
                'streamer_channel': None,
                'user_list': {},
            }
        else:
            user_list = self.get_user_list()
            user_list[self.user_name] = self.channel_name

        self.user_room[self.user_name] = self.room_name

        self.game = self.rooms[self.room_name]['game']

        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        await self.accept()

        await self.game.add_new_user(self)


    async def receive_json(self, data):
        if self.channel_name == self.get_host_channel():
            if data.get('action') == 'set_state':
                state = data['set_state']
                self.game.state = state
                if hasattr(self.game, state):
                    await getattr(self.game, state)(self)
                return

        if data.get('action') == 'handle_word':
            word = ''.join(data['word'].split()).lower()
            await self.game.make_progress(self, word)

        if data.get('action') == 'add_like':
            user_name = data.get('user_name', None)
            await self.game.add_like(self, user_name)


    async def message(self, event):
        await self.send_json(event)

    async def close_connect(self, event):
        await self.close()


    async def disconnect(self, close_code):
        if self.room_name in self.rooms:
            if self.channel_name == self.get_host_channel():
                self.rooms.pop(self.room_name)
                await self.channel_layer.group_send(self.room_name, {
                    'type': 'close_connect'
                })

        if self.room_name in self.rooms:
            self.game.counter.discard(self.user_name)
            if self.game.state in ['start_round', 'start_guessing'] and not self.game.counter:
                await self.game.send_turn_next_state(self)

            user_list = self.get_user_list()
            user_list.pop(self.user_name)

            if self.user_name == self.rooms[self.room_name]['host_name']:
                await self.channel_layer.send(self.rooms[self.room_name]['host_channel'], {
                    'type': 'message',
                    'action': 'switch_streamer_mode',
                    'streamer_mode': False,
                })
            else:
                if self.user_room.get(self.user_name) == self.room_name:
                    self.user_room.pop(self.user_name)
        else:
            if self.user_room.get(self.user_name) == self.room_name:
                self.user_room.pop(self.user_name)


        await self.channel_layer.group_discard(self.room_name, self.channel_name)
