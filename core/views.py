import random
from functools import cache
from typing import List

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import (APIException, PermissionDenied,
                                       ValidationError)
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from core.models import Match, Room, SelectedWord, Word
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
    """
    Enter authenticated player to room
    """
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
    """
    Start a match and put it in `NEWBORN` state
    """
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
def get_words_all_indices(complexity: int) -> List[int]:
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
    indices = get_words_all_indices(complexity[0])
    return Word.objects.get(pk=indices[random.randint(0, len(indices) - 1)])


def get_room_and_check_turn(
        request,
        pk,
        expected_states: List[Match.State]
):

    room = get_object_or_404(Room, pk=pk)
    players = room.players.values_list(
        'username', flat=True).order_by('username')
    if request.user.username not in players:
        raise PermissionDenied(detail='You are not member of this room')

    if not hasattr(room, 'match'):
        raise LogicError(detail='Room\'s match is not started yet')

    if room.match.state not in expected_states:
        raise LogicError(
            detail=f'Match\'s state is not in {expected_states}'
        )

    if players[room.match.current_turn] != request.user.username:
        raise PermissionDenied(detail='This is not your turn')

    return room


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def play(request, pk):
    """
    Play match and return first word

    Only the explaining player can call this endpoint.

    Return: A simple word that explaining player should explain

    """
    room = get_room_and_check_turn(request, pk, [
        Match.State.NEWBORN,
        Match.State.WAITING,
    ])

    word = get_random_word()
    SelectedWord.objects.create(
        text=word,
        match=room.match
    )

    room.match.state = Match.State.PLAYING
    room.match.round_start_time = timezone.now()
    room.match.save()

    # TODO: Notify others

    # TODO: Schedule round ending task using channel and native `await`
    # https://github.com/django/channels/issues/814#issuecomment-354708463

    return Response(
        status=status.HTTP_200_OK,
        data={'word': word.text}
    )


def add_score_to_team(room: Room, score: int, save: bool = True) -> None:
    team = None
    if room.teams == Room.Teams.ONE_TWO__THREE_FOUR:
        team = 0 if room.match.current_turn in [0, 1] else 1
    elif room.teams == Room.Teams.ONE_THREE__TWO_FOUR:
        team = 0 if room.match.current_turn in [0, 2] else 1
    elif room.teams == Room.Teams.ONE_FOUR__TWO_THREE:
        team = 0 if room.match.current_turn in [0, 3] else 1

    if team is None:
        return

    if team == 0:
        room.match.team_one_score += score
    else:
        room.match.team_two_score += score

    if save:
        room.match.save()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def correct(request, pk):
    """
    Add correct guess score to explaining player's team and get next word

    Only the explaining player can call this endpoint.

    Return: A simple word that explaining player should explain as next word

    """
    room = get_room_and_check_turn(request, pk, [
        Match.State.PLAYING,
    ])

    word = get_random_word()
    SelectedWord.objects.create(
        text=word,
        match=room.match
    )

    add_score_to_team(room, room.match.correct_guess_score)

    # TODO: Notify others

    return Response(
        status=status.HTTP_200_OK,
        data={'word': word.text}
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def skip(request, pk):
    """
    Skip current guessing word and decrease playing team score by skip penalty

    Only the explaining player can call this endpoint.

    Return: A simple word that explaining player should explain as next word

    """
    room = get_room_and_check_turn(request, pk, [
        Match.State.PLAYING,
    ])

    word = get_random_word()
    SelectedWord.objects.create(
        text=word,
        match=room.match
    )

    add_score_to_team(room, room.match.skip_penalty * -1)

    # TODO: Notify others

    return Response(
        status=status.HTTP_200_OK,
        data={'word': word.text}
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rearrange(request, pk):
    """
    Rearrange the player to different teams
    """
    room = get_object_or_404(Room, pk=pk)
    if not room.players.filter(pk=request.user.id).exists():
        raise PermissionDenied(detail='You are not member of this room')

    if room.players.count() < 4:
        raise LogicError(detail='Not enough players have joined yet')

    if hasattr(room, 'match'):
        raise LogicError(detail='Room\'s match is already started')

    teams = request.data.get('teams', None)
    if not teams or type(teams) != int or teams not in [
        Room.Teams.ONE_TWO__THREE_FOUR,
        Room.Teams.ONE_THREE__TWO_FOUR,
        Room.Teams.ONE_FOUR__TWO_THREE,
    ]:
        raise ValidationError({
            'teams': 'should be integer and between 0 to 2 inclusive'
        })

    room.teams = teams
    room.save()

    # TODO: Notify others that teams changed
    return Response(status=status.HTTP_200_OK)
