from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import (api_view, parser_classes,
                                       permission_classes)
from rest_framework.exceptions import (APIException, PermissionDenied,
                                       ValidationError)
from rest_framework.parsers import JSONParser
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Match, Room
from core.serializers import RoomSerializer


class RoomList(generics.ListCreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class RoomDetail(generics.RetrieveAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


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
            raise ValidationError(detail='Maximum room capacity exceeded')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_match(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if not room.players.filter(pk=request.user.id).exists():
        raise PermissionDenied(detail='You are not member of this room')

    if room.players.count() < 4:
        raise ValidationError(detail='Not enough players have joined yet')

    if hasattr(room, 'match'):
        raise ValidationError(detail='Room\'s match is already started')

    match = Match(
        room=room,
        state=Match.State.NEWBORN,
        current_turn=0
    )

    match.save()
    # TODO: Notify other players that match has been started
    return Response(status=status.HTTP_200_OK)
