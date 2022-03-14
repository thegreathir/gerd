# chat/routing.py
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/(?P<room_pk>\w+)', consumers.TestConsumer.as_asgi()),
]
