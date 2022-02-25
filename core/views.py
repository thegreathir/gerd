from django.db import transaction
from django.shortcuts import get_object_or_404, render
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import (APIException, PermissionDenied,
                                       ValidationError)
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from core.models import Match, Room
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


def test(request, pk):
    return render(request, 'core/test.html', {
        'room_name': pk
    })
