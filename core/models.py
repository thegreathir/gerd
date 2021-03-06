import os

from django.conf import settings
from django.core.management import call_command
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


class Word(models.Model):
    text = models.CharField(max_length=128)

    class Complexity(models.IntegerChoices):
        EASY = 1
        INTERMEDIATE = 2
        HARD = 3

    complexity = models.IntegerField(choices=Complexity.choices)

    def __str__(self):
        return self.text


class SelectedWord(models.Model):
    text = models.ForeignKey(Word, on_delete=models.CASCADE)
    match = models.ForeignKey(
        to='Match',
        on_delete=models.CASCADE,
        related_name='words',
        related_query_name='word',
    )


class Match(models.Model):
    room = models.OneToOneField(
        'Room',
        on_delete=models.CASCADE,
        primary_key=True,
    )

    class State(models.IntegerChoices):
        NEWBORN = 1
        PLAYING = 2
        WAITING = 3
        FINISHED = 4

    state = models.IntegerField(choices=State.choices)
    round_start_time = models.DateTimeField(blank=True, null=True)
    current_turn = models.IntegerField(blank=True, null=True)
    current_round = models.IntegerField(blank=True, null=True)

    team_one_score = models.IntegerField(default=0)
    team_two_score = models.IntegerField(default=0)

    total_round_count = models.IntegerField(default=8)
    round_duration_seconds = models.IntegerField(default=100)
    correct_guess_score = models.IntegerField(default=3)
    skip_penalty = models.IntegerField(default=1)


class Room(models.Model):
    name = models.CharField(max_length=128)
    players = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL,
        blank=True,
    )

    class Teams(models.IntegerChoices):
        ONE_TWO__THREE_FOUR = 1
        ONE_THREE__TWO_FOUR = 2
        ONE_FOUR__TWO_THREE = 3

    teams = models.IntegerField(
        choices=Teams.choices, default=Teams.ONE_TWO__THREE_FOUR)


class WordsFile(models.Model):
    csv_file = models.FileField(
        upload_to='wordsfiles'
    )


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=WordsFile)
def import_words_from_file(sender, instance=None, created=False, **kwargs):
    if created:
        call_command(
            'importwords',
            os.path.join(settings.MEDIA_ROOT, instance.csv_file.path)
        )
