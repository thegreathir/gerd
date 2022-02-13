from django.contrib.auth.models import User
from rest_framework import serializers

from core.models import Room4

class Room4Serializer(serializers.ModelSerializer):
    players = serializers.SlugRelatedField(
        many=True,
        queryset=User.objects.all(),
        slug_field='username'
    )
    class Meta:
        model = Room4
        fields = ['id', 'name', 'players', 'teams']