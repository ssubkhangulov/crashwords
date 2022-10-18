from django.db import models

# Create your models here.
class Word(models.Model):
    word = models.CharField('word', max_length=20)
