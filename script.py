from main.models import Word
from tqdm import tqdm
import codecs

Word.objects.all().delete()

with codecs.open('words.txt', 'r', 'utf-8') as file:
    for row in tqdm(file.readlines()):
        if len(row) <= 20:
            Word.objects.create(**{'word': row.strip()})
