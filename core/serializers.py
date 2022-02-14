from django.contrib.auth.models import User
from rest_framework import serializers

from core.models import Room, Match


class MatchSerializer(serializers.ModelSerializer):
    words = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='text'
    )
    class Meta:
        model = Match
        fields = ['words', 'state', 'start_time', 'current_turn']


class RoomSerializer(serializers.ModelSerializer):
    players = serializers.SlugRelatedField(
        many=True,
        queryset=User.objects.all(),
        slug_field='username'
    )
    match = MatchSerializer(many=False, read_only=True)
    class Meta:
        model = Room
        fields = ['id', 'name', 'players', 'teams', 'match']