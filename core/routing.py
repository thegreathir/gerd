from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'rooms/(?P<room_pk>\w+)', consumers.RoomConsumer.as_asgi()),
]
