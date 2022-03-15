from channels.generic.websocket import AsyncJsonWebsocketConsumer


class RoomConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self.group_added = False
        super().__init__(*args, **kwargs)

    async def connect(self):
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
        await self.send_json({
            'data': event['data']
        })
