import asyncio
import json
import random
import time
from typing import List

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone
from rest_framework.exceptions import APIException

from core.models import Match, Room, SelectedWord, Word


class LogicError(APIException):
    default_detail = 'Business logic error.'
    default_code = 'logic_error'


class PermissionDenied(APIException):
    default_detail = 'Permission denied.'
    default_code = 'permission_denied'


class WordSetupError(APIException):
    default_detail = 'Words are not available at the moment'
    default_code = 'words_unavailable'


@database_sync_to_async
def get_room_and_check_turn(
        user,
        pk,
        expected_states: List[Match.State]
):
    room = Room.objects.get(pk=pk)
    players = room.players.values_list(
        'username', flat=True).order_by('username')
    if user.username not in players:
        raise PermissionDenied(detail='You are not member of this room')

    if not hasattr(room, 'match'):
        raise LogicError(detail='Room\'s match is not started yet')

    if room.match.state not in expected_states:
        raise LogicError(
            detail=f'Match\'s state is not in {expected_states}'
        )

    if players[room.match.current_turn] != user.username:
        raise PermissionDenied(detail='This is not your turn')

    return room


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


@database_sync_to_async
def add_score_to_team(room: Room, score: int, save: bool = True) -> None:
    team = None
    if room.teams == Room.Teams.ONE_TWO__THREE_FOUR:
        team = 0 if room.match.current_turn in [0, 1] else 1
    elif room.teams == Room.Teams.ONE_THREE__TWO_FOUR:
        team = 0 if room.match.current_turn in [0, 2] else 1
    elif room.teams == Room.Teams.ONE_FOUR__TWO_THREE:
        team = 0 if room.match.current_turn in [0, 3] else 1

    if team is None:
        return

    if team == 0:
        room.match.team_one_score += score
    else:
        room.match.team_two_score += score

    if save:
        room.match.save()


# @cache
@database_sync_to_async
def get_words_all_indices(complexity: int) -> List[int]:
    """
    Following query result will be cached, so we should reload
    our web app after each time we modified `Word` table.
    """
    return Word.objects.filter(
        complexity=complexity
    ).values_list(
        'id',
        flat=True
    ).order_by('id')


async def get_random_word() -> Word:
    complexity = random.choices(
        [
            Word.Complexity.EASY,
            Word.Complexity.INTERMEDIATE,
            Word.Complexity.HARD,
        ],
        weights=[
            4,
            2,
            1
        ],
        k=1
    )
    indices = await get_words_all_indices(complexity[0])
    return await get_random_word_with_indices(indices)


@database_sync_to_async
def get_random_word_with_indices(indices):
    if len(indices) == 0:
        raise WordSetupError()
    return Word.objects.get(pk=indices[random.randint(0, len(indices) - 1)])


@database_sync_to_async
def play_room_match(room):
    room.match.state = Match.State.PLAYING
    room.match.round_start_time = timezone.now()
    room.match.save()


@database_sync_to_async
def finish_room_match_round(room):
    room.match.state = Match.State.WAITING
    room.match.current_round += 1
    room.match.current_turn = (room.match.current_round + 1) % 4
    room.match.save()


class TestConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_pk = int(self.scope['url_route']['kwargs']['pk'])
        self.user = self.scope['user']
        self.room_group_name = 'room_%d' % self.room_pk

        # TODO: check user-related stuff (auth? room-related?)
        if not self.user.is_authenticated:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive_json(self, data):
        action = data.get('action')
        if not action:
            return
        try:
            if action == 'play':
                await self.play()
            if action == 'skip':
                await self.skip()
            if action == 'correct':
                await self.correct()
        except Exception as e:
            await self.send_json({
                'message': str(e)
            })

    # Receive message from room group
    async def room_event(self, event):
        if 'error' in event:
            await self.send(text_data=json.dumps({
                'message': event['error']
            }))
            return

        message = event['message']
        if await is_guessing(self.user, self.room_pk):
            message = "<-Guessing->"
        # Send message to WebSocket
        await self.send_json({
            'message': message
        })

    async def finish_round(self, on):
        await asyncio.sleep(on - time.time())

        # TODO: New Round
        room = await database_sync_to_async(
            lambda: Room.objects.get(pk=self.room_pk)
        )()
        await finish_room_match_round(room)

        await self.send_json({
            'type': 'room_event',
            'message': 'round finished'
        })

    async def play(self):
        """
        Play match and return first word

        Only the explaining player can call this endpoint.

        Return: A simple word that explaining player should explain

        """
        room = await get_room_and_check_turn(self.user, self.room_pk, [
            Match.State.NEWBORN,
            Match.State.WAITING,
        ])

        word = await get_random_word()
        await database_sync_to_async(lambda: SelectedWord.objects.create(
            text=word,
            match=room.match
        ))()

        await play_room_match(room)

        # TODO: Notify others
        await self.channel_layer.group_send(self.room_group_name, {
            'type':    'room_event',
            'message': word.text
        })

        asyncio.create_task(self.finish_round(int(time.time()) + 30))

        # TODO: Schedule round ending task using channel and native `await`
        # https://github.com/django/channels/issues/814#issuecomment-354708463

    async def correct(self):
        """
        Add correct guess score to explaining player's team and get next word

        Only the explaining player can call this endpoint.

        Return: A simple word that explaining player should explain
        as next word

        """
        room = await get_room_and_check_turn(self.user, self.room_pk, [
            Match.State.PLAYING,
        ])

        word = await get_random_word()
        await database_sync_to_async(lambda: SelectedWord.objects.create(
            text=word,
            match=room.match
        ))()

        add_score_to_team(room, room.match.correct_guess_score)

        # TODO: Notify others
        await self.channel_layer.group_send(self.room_group_name, {
            'type':    'room_event',
            'message': word.text
        })

    async def skip(self):
        """
        Skip current guessing word and decrease playing team score
        by skip penalty

        Only the explaining player can call this endpoint.

        Return: A simple word that explaining player should explain
        as next word

        """
        room = await get_room_and_check_turn(self.user, self.room_pk, [
            Match.State.PLAYING,
        ])

        word = await get_random_word()
        await database_sync_to_async(lambda: SelectedWord.objects.create(
            text=word,
            match=room.match
        ))()

        add_score_to_team(room, room.match.skip_penalty * -1)

        # TODO: Notify others
        await self.channel_layer.group_send(self.room_group_name, {
            'type':    'room_event',
            'message': word.text
        })
