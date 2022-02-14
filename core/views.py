from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import (api_view, parser_classes,
                                       permission_classes)
from rest_framework.parsers import JSONParser
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Room, Match
from core.serializers import RoomSerializer


class RoomList(generics.ListCreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class RoomDetail(generics.RetrieveAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


class RoomCapacityExceededError(Exception):
    pass


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_to_room(request, pk):
    try:
        with transaction.atomic():
            room = Room.objects.get(pk=pk)

            if room.players.count() < 4:
                room.players.add(request.user)
                room.save()
                # TODO: Notify other players in room
                return Response(status=status.HTTP_200_OK)
            else:
                raise RoomCapacityExceededError()
    except Room.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    except RoomCapacityExceededError:
        return Response(data={
            'message': 'Maximum room capacity exceeded'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_match(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if not room.players.filter(pk=request.user.id).exists():
        return Response(data={
            'message': 'You are not member of this room'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if room.players.count() < 4:
        return Response(data={
            'message': 'Not enough players have joined'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if hasattr(room, 'match'):
        return Response(data={
            'message': 'Room\'s match is already started'
        }, status=status.HTTP_400_BAD_REQUEST)

    match = Match(
        room=room,
        state=Match.State.NEWBORN,
        current_turn=0
    )

    match.save()
    # TODO: Notify other players that match has been started
    return Response(status=status.HTTP_200_OK)
