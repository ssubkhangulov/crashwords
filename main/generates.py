import string
import random

def generate_room_name():
    room_name = ''.join([random.choice(string.ascii_letters).upper() for _ in range(4)])
    return room_name

def choose_word():
    word = random.choice(['яблоко', 'груша', 'банан', 'виноград'])
    return word
