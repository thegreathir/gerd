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

from core.models import Room4
from core.serializers import Room4Serializer


class Room4List(generics.ListCreateAPIView):
    queryset = Room4.objects.all()
    serializer_class = Room4Serializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class Room4Detail(generics.RetrieveAPIView):
    queryset = Room4.objects.all()
    serializer_class = Room4Serializer


@transaction.atomic
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_to_room(request, pk):
    try:
        room = Room4.objects.get(pk=pk)
    except Room4.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if room.players.count() < 4:
        room.players.add(request.user)
        room.save()
        return Response(status=status.HTTP_200_OK)
    else:
        return Response(data={
            'error': 'Maximum room capacity exceeded'
        }, status=status.HTTP_400_BAD_REQUEST)
