import json
import asyncio
from collections import deque
import string
import itertools
import random

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Word

from .generates import choose_word


class Game():
    rooms = set()
    def __init__(self, room_name):
        self.state = 'pause'
        self.queue = deque()
        self.guesser = ''
        self.word = ''
        self.clues = {}
        self.crashed_clues = {}
        self.guess = ''
        self.counter = set()
        self.likes = set()
        self.results = {}

    def choose_guesser(self, user):
        user_list = [user.rooms[user.room_name]['host_name']] + list(user.get_user_list().keys())
        if not user_list:
            return

        self.guesser = ''
        while (self.guesser not in set(user_list)):
            if not self.queue:
                self.queue = deque(user_list)
            self.guesser = self.queue.popleft()
        return


    async def send_start_round(self, user, user_name, channel_name):
        await user.channel_layer.send(channel_name, {
            'type': 'message',
            'action': 'set_state',
            'set_state': self.state,
            'guesser_name': self.guesser,
            'word': None if user_name == self.guesser else self.word,
        })
        await self.send_table(user, channel_name)


    async def start_round(self, user):
        for word in self.clues:
            for user_name in self.clues[word]:
                self.results[user_name]['clues'] += 1
                if len(self.clues[word]) != 1:
                    self.results[user_name]['crashes'] += 1

        self.word = random.choice(await sync_to_async(list)(Word.objects.all())).word
        self.choose_guesser(user)

        self.clues = {}
        self.guess = ''
        self.likes = set()

        self.counter = set(user.get_user_list())
        self.counter.discard(self.guesser)

        for (user_name, channel_name) in user.get_all_user():
            await self.send_start_round(user, user_name, channel_name)

        self.results[self.guesser]['guesses'] += 1


    async def send_start_guessing(self, user, user_name, channel_name):
        await user.channel_layer.send(channel_name, {
            'type': 'message',
            'action': 'set_state',
            'set_state': self.state,
            'guesser_name': self.guesser,
            'clues': self.clues,
            'crashed_clues': list(self.crashed_clues.values()),
        })

    async def start_guessing(self, user):
        self.crashed_clues = {}
        for word in list(self.clues):
            if len(self.clues[word]) != 1:
                self.crashed_clues[word] = self.clues.pop(word)

        self.counter = set([self.guesser] if user.user_room.get(self.guesser) == user.room_name else [])
        for (user_name, channel_name) in user.get_all_user():
            await self.send_start_guessing(user, user_name, channel_name)
        if not self.counter:
            await self.send_turn_next_state(user)


    async def send_show_result(self, user, user_name, channel_name):
        await user.channel_layer.send(channel_name, {
            'type': 'message',
            'action': 'set_state',
            'set_state': self.state,
            'guesser_name': self.guesser,
            'clues': self.clues,
            'crashed_clues': self.crashed_clues,
            'word': self.word,
            'guess': self.guess,
        })

    async def show_result(self, user):
        for (user_name, channel_name) in user.get_all_user():
            await self.send_show_result(user, user_name, channel_name)


    async def send_add_clue(self, user, word):
        await user.channel_layer.group_send(user.room_name, {
            'type': 'message',
            'action': 'add_clue',
            'user_name': user.user_name,
            'clue': self.clues.get(word, []),
        })


    async def send_turn_next_state(self, user):
        await user.channel_layer.send(user.get_host_channel(), {
            'type': 'message',
            'action': 'turn_next_state',
            'current_state': self.state,
        })

    async def make_progress(self, user, word):
        if self.state == 'start_round' and  user.user_name != self.guesser:
            self.clues.setdefault(word, [])
            self.clues[word].append(user.user_name)
            await self.send_add_clue(user, word)
            self.counter.discard(user.user_name)
            if not self.counter:
                await self.send_turn_next_state(user)
            return

        if self.state == 'start_guessing' and user.user_name == self.guesser:
            self.guess = word
            if self.guess == self.word:
                self.results[self.guesser]['right_guesses'] += 1
            self.counter.discard(user.user_name)
            if not self.counter:
                await self.send_turn_next_state(user)
            return


    async def add_like(self, user, user_name_2):
        user_name_1 = user.user_name
        if user_name_2 not in self.results or user_name_1 == user_name_2:
            return

        message = {
            'type': 'message',
            'action': 'change_like_count',
            'change_type': 0,
            'user_name': user_name_2,
        }
        if (user_name_1, user_name_2) in self.likes:
            self.likes.discard((user_name_1, user_name_2))
            self.results[user_name_2]['score'] = self.results[user_name_2]['score'] - 1
            message['change_type'] = -1
        else:
            self.likes.add((user_name_1, user_name_2))
            self.results[user_name_2]['score'] = self.results[user_name_2]['score'] + 1
            message['change_type'] = 1

        await user.channel_layer.group_send(user.room_name, message)


    async def send_table(self, user, channel_name):
        message = {
            'type': 'message',
            'action': 'show_table',
            'table': list(self.results.values()),
        }
        await user.channel_layer.send(channel_name, message)


    async def add_new_user(self, user):
        self.counter.add(user.user_name)
        state_list = {
            'start_round': self.send_start_round,
            'start_guessing': self.send_start_guessing,
            'show_result': self.send_show_result,
        }
        if self.state in list(state_list):
            await state_list[self.state](user, user.user_name, user.channel_name)

        await self.send_table(user, user.channel_name)

        if user.user_name not in self.results:
            self.queue.append(user.user_name)
            self.results.setdefault(user.user_name, {
                'user_name': user.user_name,
                'score': 0,
                'crashes': 0,
                'clues': 0,
                'right_guesses': 0,
                'guesses': 0,
            })
            message = dict(self.results[user.user_name])
            message['type'] = 'message'
            message['action'] = 'add_user'
            await user.channel_layer.group_send(user.room_name, message)
