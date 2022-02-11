from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

# Create your models here.


class Word(models.Model):
    text = models.CharField(max_length=128)

    class Compexity(models.IntegerChoices):
        EASY = 1
        INTERMEDIATE = 2
        HARD = 3

    compexity = models.IntegerField(choices=Compexity.choices)


class Match4(models.Model):
    players = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL,
        blank=True,
    )

    words = models.ManyToManyField(
        to=Word,
        blank=True,
    )

    class State(models.IntegerChoices):
        NEWBORN = 1
        STARTED = 2
        FINISHED = 3

    state = models.IntegerField(choices=State.choices)
    start_time = models.DateTimeField(blank=True, null=True)
    current_turn = models.IntegerField(blank=True, null=True)

    def clean(self, *args, **kwargs):
        if self.players.count() > 4:
            raise ValidationError(
                "More than 4 players attached")
        if self.current_turn >= 4:
            raise ValidationError(
                "Out of range turn")

        super(Match4, self).clean(*args, **kwargs)
