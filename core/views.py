from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from core.serializers import Room4Serializer
from core.models import Room4


class Room4List(generics.ListCreateAPIView):
    queryset = Room4.objects.all()
    serializer_class = Room4Serializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class Room4Detail(generics.RetrieveAPIView):
    queryset = Room4.objects.all()
    serializer_class = Room4Serializer
