from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from core.models import Room


@database_sync_to_async
def is_guessing(
    user,
    pk
):
    room = Room.objects.get(pk=pk)
    players = room.players.values_list(
        'username', flat=True).order_by('username')
    guesser_index = (room.match.current_turn + 2) % 4
    return players[guesser_index] == user.username


class TestConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self.group_added = False
        super().__init__(args, kwargs)

    async def connect(self):
        # TODO: check user-related stuff (auth? room-related?)
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        url_room_pk = int(self.scope['url_route']['kwargs']['room_pk'])
        self.room_pk = int(self.scope['room_pk'])

        if url_room_pk != self.room_pk:
            await self.close()
            return

        self.room_group_name = 'room_%d' % self.room_pk

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        self.group_added = True

        await self.accept()

    async def disconnect(self, close_code):
        if not self.group_added:
            return
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from room group
    async def room_event(self, event):
        data = event['data']
        if 'word' in data:
            if await is_guessing(self.user, self.room_pk):
                data['word'] = '<-Guessing->'

        # Send message to WebSocket
        await self.send_json({
            'data': data
        })
