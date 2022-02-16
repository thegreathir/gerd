import random
from typing import List
from functools import cache
from datetime import datetime

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from core.models import Match, Room, Word, SelectedWord
from core.serializers import RoomSerializer


class RoomList(generics.ListCreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class RoomDetail(generics.RetrieveAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


class LogicError(APIException):
    status_code = 400
    default_detail = 'Business logic error.'
    default_code = 'logic_error'


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_room(request, pk):
    with transaction.atomic():
        room = get_object_or_404(Room, pk=pk)

        if room.players.filter(pk=request.user.pk).exists():
            return Response(status=status.HTTP_200_OK)

        if room.players.count() < 4:
            room.players.add(request.user)
            room.save()
            # TODO: Notify other players in room
            return Response(status=status.HTTP_200_OK)
        else:
            raise LogicError(detail='Maximum room capacity exceeded')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_match(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if not room.players.filter(pk=request.user.id).exists():
        raise PermissionDenied(detail='You are not member of this room')

    if room.players.count() < 4:
        raise LogicError(detail='Not enough players have joined yet')

    if hasattr(room, 'match'):
        raise LogicError(detail='Room\'s match is already started')

    match = Match(
        room=room,
        state=Match.State.NEWBORN,
        current_turn=0,
        current_round=0
    )

    match.save()
    # TODO: Notify other players that match has been started
    return Response(status=status.HTTP_200_OK)


@cache
def get_all_indices(complexity: int) -> List[int]:
    """
    Following query result will be cached, so we should reload
    our web app after each time we modified `Word` table.
    """
    return Word.objects.filter(complexity=complexity).values_list(
        'id', flat=True).order_by('id')


def get_random_word() -> Word:
    complexity = random.choices(
        [
            Word.Complexity.EASY,
            Word.Complexity.INTERMEDIATE,
            Word.Complexity.HARD,
        ],
        weights=[
            4,
            2,
            1
        ],
        k=1
    )
    indices = get_all_indices(complexity[0])
    return Word.objects.get(pk=indices[random.randint(0, len(indices) - 1)])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def play(request, pk):
    room = get_object_or_404(Room, pk=pk)
    players = room.players.values_list(
        'username', flat=True).order_by('username')
    if request.user.username not in players:
        raise PermissionDenied(detail='You are not member of this room')

    if not hasattr(room, 'match'):
        raise LogicError(detail='Room\'s match is not started yet')

    if room.match.state != Match.State.NEWBORN and \
            room.match.state != Match.State.WAITING:
        raise LogicError(detail='State is not newborn nor waiting')

    if players[room.match.current_turn] != request.user.username:
        raise PermissionDenied(detail='This is not your turn')

    word = get_random_word()
    SelectedWord.objects.create(
        text=word,
        match=room.match
    )

    room.match.state = Match.State.PLAYING
    room.match.round_start_time = datetime.now()
    room.match.save()

    return Response(
        status=status.HTTP_200_OK,
        data={'word': word.text}
    )
