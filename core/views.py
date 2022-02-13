from django.db import transaction
from django.http import Http404
from rest_framework import generics, status
from rest_framework.decorators import (api_view, parser_classes,
                                       permission_classes)
from rest_framework.parsers import JSONParser
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Room
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
            'error': 'Maximum room capacity exceeded'
        }, status=status.HTTP_400_BAD_REQUEST)
