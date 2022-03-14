from urllib.parse import parse_qs

import jwt
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User

from core.models import Room


@database_sync_to_async
def get_user_and_room(username, room_pk):
    user = User.objects.get(username=username)
    room = Room.objects.get(pk=room_pk)
    if not room.players.filter(pk=user.id).exists():
        raise Exception("user not in room")
    return user, room


class TicketAuthMiddleware:
    """
    Token authorization middleware for Django Channels 2
    """

    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode("utf-8"))
        if "ticket" in query_string:
            ticket = query_string["ticket"][0]
            try:
                token = jwt.decode(ticket, settings.TICKET_SECRET,
                                   algorithms=["HS256"])
                user, room = await get_user_and_room(
                    token["username"], token["room"])
                scope['user'] = user
                scope['room_pk'] = room.pk
            except Exception:
                scope['user'] = AnonymousUser()
        return await self.app(scope, receive, send)


def TicketAuthMiddlewareStack(inner): return TicketAuthMiddleware(
    AuthMiddlewareStack(inner)
)
