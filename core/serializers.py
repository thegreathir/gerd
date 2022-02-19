from django.contrib.auth.models import User
from rest_framework import serializers

from core.models import Match, Room, SelectedWord


class SelectedWordSerializer(serializers.ModelSerializer):
    text = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field='text'
    )

    class Meta:
        model = SelectedWord
        fields = ['text']


class MatchSerializer(serializers.ModelSerializer):
    words = SelectedWordSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Match
        fields = [
            'words',
            'state',
            'round_start_time',
            'current_turn',
            'current_round',
            'total_round_count',
            'round_duration_seconds',
            'team_one_score',
            'team_two_score',
            'correct_guess_score',
            'skip_penalty',
        ]


class RoomSerializer(serializers.ModelSerializer):
    players = serializers.SlugRelatedField(
        many=True,
        queryset=User.objects.all(),
        slug_field='username',
    )
    match = MatchSerializer(many=False, read_only=True)

    class Meta:
        model = Room
        fields = ['id', 'name', 'players', 'teams', 'match']
