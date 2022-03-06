import json
import random
import time
from copy import deepcopy
from typing import Dict, List, Tuple
from unittest import mock

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase

from core.models import Match, Room, Word
from core.views import get_words_all_indices


def get_equipped_test_case(base=APITestCase):
    class EquippedTestCase(base):
        def setUp(self):
            get_words_all_indices.cache_clear()

            self.users: Dict[str, User] = dict()

            self.words = [
                ('multiply', random.randint(1, 3)),
                ('abiding', random.randint(1, 3)),
                ('mask', random.randint(1, 3)),
                ('trace', random.randint(1, 3)),
                ('selection', random.randint(1, 3)),
                ('real', random.randint(1, 3)),
                ('pop', random.randint(1, 3)),
                ('protective', random.randint(1, 3)),
                ('certain', random.randint(1, 3)),
                ('second', random.randint(1, 3)),
                ('silly', random.randint(1, 3)),
                ('sign', random.randint(1, 3)),
                ('redo', random.randint(1, 3)),
                ('middle', random.randint(1, 3)),
                ('stale', random.randint(1, 3)),
                ('daily', random.randint(1, 3)),
                ('labored', random.randint(1, 3)),
                ('broken', random.randint(1, 3)),
                ('parsimonious', random.randint(1, 3)),
                ('bite', random.randint(1, 3)),
                ('forecast', random.randint(1, 3)),
                ('aquatic', random.randint(1, 3)),
            ]

        def create_user(self, username: str = 'user') -> None:
            if username in self.users.keys():
                return

            self.users[username] = User.objects.create(
                username=username, password='p@@@@$w00rdd')

        def create_sample_room(
            self,
            name: str = 'Room1',
            creator: str = 'user'
        ) -> None:
            response = self.client.post(
                reverse('rooms'),
                data={
                    'name': name,
                    'players': []
                },
                HTTP_AUTHORIZATION=f'Token {self.users[creator].auth_token}',
                format='json'
            )

            self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        def join_room(self, username: str, room_id: int = 1) -> None:
            response = self.client.post(
                reverse('join-room', args=[room_id]),
                HTTP_AUTHORIZATION=f'Token {self.users[username].auth_token}',
            )
            self.assertEqual(status.HTTP_200_OK, response.status_code)

        def start_match(self, player: str = 'user', room_id: int = 1) -> None:
            response = self.client.post(
                reverse('start-room-match', args=[room_id]),
                HTTP_AUTHORIZATION=f'Token {self.users[player].auth_token}',
            )

            self.assertEqual(status.HTTP_200_OK, response.status_code)

        def create_words(self, words: List[Tuple[str, int]]) -> None:
            for word, complexity in words:
                Word.objects.create(text=word, complexity=complexity)

        def remove_words(self) -> None:
            Word.objects.all().delete()

        def get_room(self, room_id: int = 1):
            response = self.client.get(reverse('room-detail', args=[room_id]))
            self.assertEqual(status.HTTP_200_OK, response.status_code)
            return response

        def get_explaining_player(self, room_id: int = 1):
            response = self.get_room(room_id)

            players = deepcopy(response.data['players'])
            players.sort()

            return players[response.data['match']['current_turn']]

        @staticmethod
        def print_response_data(response):
            print('\n')
            print(json.dumps(response.data, indent=4))

    return EquippedTestCase


class RoomCreateTestCase(get_equipped_test_case()):
    def setUp(self):
        super().setUp()

        self.create_user()
        self.user = self.users['user']

    def test_authenticated_user_can_create_room(self):
        response = self.client.post(
            reverse('rooms'),
            data={
                'name': 'Room1',
                'players': []
            },
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}',
            format='json'
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_anonymous_user_can_not_create_room(self):
        response = self.client.post(
            reverse('rooms'),
            data={
                'name': 'Room1',
                'players': []
            },
            format='json'
        )

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_created_room_can_be_fetched(self):
        response = self.client.post(
            reverse('rooms'),
            data={
                'name': 'Room1',
                'players': []
            },
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}',
            format='json'
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response = self.client.get(
            reverse('room-detail', args=[1])
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIsNone(response.data['match'])
        self.assertEqual(response.data['name'], 'Room1')

        response = self.client.get(
            reverse('rooms')
        )

        self.assertEqual(1, len(response.data))
        self.assertEqual('Room1', response.data[0]['name'])

    def test_user_can_add_herself_at_room_creation_time(self):
        response = self.client.post(
            reverse('rooms'),
            data={
                'name': 'Room1',
                'players': [self.user.username]
            },
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}',
            format='json'
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response = self.client.get(
            reverse('room-detail', args=[1])
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual([self.user.username], response.data['players'])

    def test_user_can_not_add_not_existed_user_at_creation_time(self):
        response = self.client.post(
            reverse('rooms'),
            data={
                'name': 'Room1',
                'players': ['random_username']
            },
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}',
            format='json'
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual('does_not_exist', response.data['players'][0].code)


class JoinRoomTestCase(get_equipped_test_case()):

    def setUp(self):
        super().setUp()
        self.create_user(username='user1')
        self.create_user(username='user2')
        self.create_user(username='user3')
        self.create_user(username='user4')
        self.create_user(username='user5')

        for k, v in self.users.items():
            setattr(self, k, v)
        self.create_sample_room(creator='user1')

    def test_new_player_can_join_existed_room(self):
        response = self.client.post(
            reverse('join-room', args=[1]),
            HTTP_AUTHORIZATION=f'Token {self.user2.auth_token}',
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTrue(Room.objects.get(
            pk=1).players.filter(username='user2').exists())

    def test_player_can_not_join_not_existed_room(self):
        response = self.client.post(
            reverse('join-room', args=[2]),
            HTTP_AUTHORIZATION=f'Token {self.user2.auth_token}',
        )

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_anonymous_user_can_not_join_any_room(self):
        response = self.client.post(
            reverse('join-room', args=[1]),
        )

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_over_4_players_can_not_join_a_single_room(self):
        self.join_room('user1')
        self.join_room('user2')
        self.join_room('user3')
        self.join_room('user4')

        response = self.client.post(
            reverse('join-room', args=[1]),
            HTTP_AUTHORIZATION=f'Token {self.user5.auth_token}',
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn('exceeded', response.data['detail'])

    def test_multiple_join_is_ok(self):
        self.join_room('user1')
        self.join_room('user1')
        self.join_room('user1')
        self.join_room('user2')
        self.join_room('user3')
        self.join_room('user4')
        self.join_room('user4')

        self.assertEqual(4, Room.objects.get(pk=1).players.count())


class RearrangeTestCase(get_equipped_test_case()):

    def setUp(self):
        super().setUp()
        for i in range(6):
            self.create_user(username=f'user{i}')

        self.create_sample_room(creator='user1')

    def test_joined_player_can_rearrange_teams_of_completed_room(self):
        self.join_room('user1')
        self.join_room('user2')
        self.join_room('user3')
        self.join_room('user4')

        new_teams = random.randint(1, 2)
        response = self.client.post(
            reverse('rearrange', args=[1]),
            data={
                'teams': new_teams
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.users["user1"].auth_token}',
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(Room.objects.get(pk=1).teams, new_teams)

    def test_joined_player_can_not_rearrange_with_invalid_input(self):
        self.join_room('user1')
        self.join_room('user2')
        self.join_room('user3')
        self.join_room('user4')

        new_teams = 10
        response = self.client.post(
            reverse('rearrange', args=[1]),
            data={
                'teams': new_teams
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.users["user1"].auth_token}',
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn('between', response.data['teams'])

        new_teams = 'two'
        response = self.client.post(
            reverse('rearrange', args=[1]),
            data={
                'teams': new_teams
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.users["user1"].auth_token}',
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn('integer', response.data['teams'])

    def test_player_can_not_rearrange_when_match_is_started(self):
        self.join_room('user1')
        self.join_room('user2')
        self.join_room('user3')
        self.join_room('user4')

        self.start_match(player='user1')

        response = self.client.post(
            reverse('rearrange', args=[1]),
            data={
                'teams': 2
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.users["user1"].auth_token}',
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn('started', response.data['detail'])

    def test_player_can_not_rearrange_when_not_enough_players_joined(self):
        self.join_room('user1')
        self.join_room('user2')
        self.join_room('user3')

        response = self.client.post(
            reverse('rearrange', args=[1]),
            data={
                'teams': 2
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.users["user1"].auth_token}',
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn('joined', response.data['detail'])

    def test_not_joined_player_can_not_rearrange(self):
        self.join_room('user1')
        self.join_room('user2')
        self.join_room('user3')
        self.join_room('user4')

        response = self.client.post(
            reverse('rearrange', args=[1]),
            data={
                'teams': 2
            },
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.users["user5"].auth_token}',
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertIn('member', response.data['detail'])


class StartMatchTestCase(get_equipped_test_case()):

    def setUp(self):
        super().setUp()
        for i in range(6):
            self.create_user(username=f'user{i}')

        self.create_sample_room(creator='user1')

    def test_match_can_be_started_in_completed_room(self):
        self.join_room('user1')
        self.join_room('user2')
        self.join_room('user3')
        self.join_room('user4')

        user_id: int = random.randint(1, 4)
        token = self.users[f'user{user_id}'].auth_token
        response = self.client.post(
            reverse('start-room-match', args=[1]),
            HTTP_AUTHORIZATION=f'Token {token}',
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response = self.client.get(
            reverse('room-detail', args=[1])
        )

        self.assertIsNotNone(response.data['match'])
        self.assertEqual(1, response.data['match']['state'])

    def test_match_with_not_enough_players_can_not_be_started(self):
        self.join_room('user1')
        self.join_room('user2')
        self.join_room('user3')

        response = self.client.post(
            reverse('start-room-match', args=[1]),
            HTTP_AUTHORIZATION=f'Token {self.users["user1"].auth_token}',
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn('enough', response.data['detail'])

    def test_not_joined_player_can_not_start_the_match(self):
        self.join_room('user1')
        self.join_room('user2')
        self.join_room('user3')
        self.join_room('user4')

        response = self.client.post(
            reverse('start-room-match', args=[1]),
            HTTP_AUTHORIZATION=f'Token {self.users["user5"].auth_token}',
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertIn('not member', response.data['detail'])

    def test_match_can_not_be_started_twice(self):
        self.join_room('user1')
        self.join_room('user2')
        self.join_room('user3')
        self.join_room('user4')

        response = self.client.post(
            reverse('start-room-match', args=[1]),
            HTTP_AUTHORIZATION=f'Token {self.users["user1"].auth_token}',
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response = self.client.post(
            reverse('start-room-match', args=[1]),
            HTTP_AUTHORIZATION=f'Token {self.users["user1"].auth_token}',
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn('started', response.data['detail'])


class PlayMatchTestCase(get_equipped_test_case()):

    def setUp(self):
        super().setUp()
        self.create_words(self.words)

        for i in range(6):
            self.create_user(username=f'user{i}')

        self.create_sample_room(creator='user1')

        self.join_room('user1')
        self.join_room('user2')
        self.join_room('user3')
        self.join_room('user4')

    @mock.patch('core.views.finish_round', lambda *x, **y: ...)
    def test_explaining_player_cannot_play_with_no_words(self):
        self.remove_words()
        self.start_match('user1')

        explaining_player = self.get_explaining_player()

        token = self.users[explaining_player].auth_token
        response = self.client.post(
            reverse('play', args=[1]),
            HTTP_AUTHORIZATION=f'Token {token}',
        )

        self.assertEqual(status.HTTP_503_SERVICE_UNAVAILABLE,
                         response.status_code)

    @mock.patch('core.views.finish_round', lambda *x, **y: ...)
    def test_explaining_player_can_call_play(self):
        self.start_match('user1')

        explaining_player = self.get_explaining_player()

        token = self.users[explaining_player].auth_token
        response = self.client.post(
            reverse('play', args=[1]),
            HTTP_AUTHORIZATION=f'Token {token}',
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIn(response.data['word'], list(zip(*self.words))[0])
        word = response.data['word']

        response = self.client.get(reverse('room-detail', args=[1]))

        self.assertEqual(word, response.data['match']['words'][0]['text'])
        self.assertEqual(Match.State.PLAYING, response.data['match']['state'])

    def start_and_play(self, starter: str = 'user1'):
        self.start_match(starter)

        explaining_player = self.get_explaining_player()

        token = self.users[explaining_player].auth_token
        response = self.client.post(
            reverse('play', args=[1]),
            HTTP_AUTHORIZATION=f'Token {token}',
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        return response

    @mock.patch('core.views.finish_round', lambda *x, **y: ...)
    def test_players_can_not_call_play_twice(self):
        self.start_and_play()

        explaining_player = self.get_explaining_player()
        token = self.users[explaining_player].auth_token
        response = self.client.post(
            reverse('play', args=[1]),
            HTTP_AUTHORIZATION=f'Token {token}',
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn('state', response.data['detail'])

    @mock.patch('core.views.finish_round', lambda *x, **y: ...)
    def test_explaining_player_can_call_correct(self):
        response = self.start_and_play()
        word1 = response.data['word']

        explaining_player = self.get_explaining_player()
        token = self.users[explaining_player].auth_token
        response = self.client.post(
            reverse('correct', args=[1]),
            HTTP_AUTHORIZATION=f'Token {token}',
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        word2 = response.data['word']

        response = self.get_room()

        self.assertEqual(
            Room.objects.get(pk=1).match.correct_guess_score,
            response.data['match']['team_one_score']
        )

        self.assertEqual(
            0,
            response.data['match']['team_two_score']
        )

        self.assertEqual(word1, response.data['match']['words'][0]['text'])
        self.assertEqual(word2, response.data['match']['words'][1]['text'])

    @mock.patch('core.views.finish_round', lambda *x, **y: ...)
    def test_explaining_player_can_call_skip(self):
        self.start_and_play()

        explaining_player = self.get_explaining_player()
        token = self.users[explaining_player].auth_token
        response = self.client.post(
            reverse('skip', args=[1]),
            HTTP_AUTHORIZATION=f'Token {token}',
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        word = response.data['word']

        response = self.get_room()

        self.assertEqual(
            Room.objects.get(pk=1).match.skip_penalty * -1,
            response.data['match']['team_one_score']
        )

        self.assertEqual(
            0,
            response.data['match']['team_two_score']
        )
        self.assertEqual(word, response.data['match']['words'][-1]['text'])

    @mock.patch('core.views.finish_round', lambda *x, **y: ...)
    def test_not_explaining_player_can_not_call_correct(self):
        self.start_and_play()

        response = self.get_room(1)

        players = deepcopy(response.data['players'])
        players.sort()

        not_explaining_player = players[
            (response.data['match']['current_turn'] + 1) % 4
        ]

        token = self.users[not_explaining_player].auth_token
        response = self.client.post(
            reverse('correct', args=[1]),
            HTTP_AUTHORIZATION=f'Token {token}',
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @mock.patch('core.views.finish_round', lambda *x, **y: ...)
    def test_not_explaining_player_can_not_call_skip(self):
        self.start_and_play()

        response = self.get_room(1)

        players = deepcopy(response.data['players'])
        players.sort()

        not_explaining_player = players[
            (response.data['match']['current_turn'] + 1) % 4
        ]

        token = self.users[not_explaining_player].auth_token
        response = self.client.post(
            reverse('skip', args=[1]),
            HTTP_AUTHORIZATION=f'Token {token}',
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)


class RoundTestCase(get_equipped_test_case(APITransactionTestCase)):

    def setUp(self):
        super().setUp()
        for i in range(6):
            self.create_user(username=f'user{i}')

        self.create_sample_room(creator='user1')

        self.join_room('user1')
        self.join_room('user2')
        self.join_room('user3')
        self.join_room('user4')

        self.create_words(self.words)

    def test_round_will_finish(self):
        self.start_match('user1')

        round_duration = 1
        total_round = random.randint(5, 10)
        match = Match.objects.get(pk=1)
        match.round_duration_seconds = round_duration
        match.total_round_count = total_round
        match.save()

        for i in range(total_round):
            current_round = i + 1
            last_round = (current_round == total_round)

            explaining_player = self.get_explaining_player()
            token = self.users[explaining_player].auth_token
            response = self.client.post(
                reverse('play', args=[1]),
                HTTP_AUTHORIZATION=f'Token {token}',
            )

            self.assertEqual(status.HTTP_200_OK, response.status_code)

            time.sleep(round_duration + 1)

            response = self.get_room()
            self.assertEqual(
                Match.State.FINISHED if last_round else Match.State.WAITING,
                response.data['match']['state']
            )
            if not last_round:
                self.assertEqual(
                    current_round % 4,
                    response.data['match']['current_turn']
                )
                self.assertEqual(
                    current_round + 1,
                    response.data['match']['current_round']
                )
