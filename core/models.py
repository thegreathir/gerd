from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


class Word(models.Model):
    text = models.CharField(max_length=128)

    class Compexity(models.IntegerChoices):
        EASY = 1
        INTERMEDIATE = 2
        HARD = 3

    compexity = models.IntegerField(choices=Compexity.choices)


class Match4(models.Model):
    room = models.ForeignKey("Room4", models.CASCADE)

    words = models.ManyToManyField(
        to=Word,
        blank=True,
    )

    class State(models.IntegerChoices):
        NEWBORN = 1
        STARTED = 2
        PAUSED = 3
        FINISHED = 4

    state = models.IntegerField(choices=State.choices)
    start_time = models.DateTimeField(blank=True, null=True)
    current_turn = models.IntegerField(blank=True, null=True)

    def clean(self, *args, **kwargs):
        if self.current_turn >= 4:
            raise ValidationError(
                "Out of range turn")

        super(Match4, self).clean(*args, **kwargs)


class Room4(models.Model):
    name = models.CharField(max_length=128)
    players = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL,
        blank=True,
    )

    class Teams(models.IntegerChoices):
        ONE_TWO__THREE_FOUR = 1
        ONE_THREE__TWO_FOUR = 2
        ONE_FOUR__TWO_THREE = 3

    teams = models.IntegerField(choices=Teams.choices, default=Teams.ONE_TWO__THREE_FOUR)

    def clean(self, *args, **kwargs):
        if self.players.count() > 4:
            raise ValidationError(
                "More than 4 players attached")

        super(Match4, self).clean(*args, **kwargs)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
