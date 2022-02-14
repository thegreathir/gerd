from django.urls import reverse
from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.test import APITestCase
from rest_framework import status


class RoomCreateTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='user1', password='p@@@@$w00rdd')

    def test_authenticated_can_create_room(self):
        response = self.client.post(
            reverse('rooms'),
            data={
                'name': 'Room1',
                'players': []
            },
            HTTP_AUTHORIZATION=f"Token {self.user.auth_token}",
            format='json'
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

    def test_unauthenticated_can_not_create_room(self):
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
            HTTP_AUTHORIZATION=f"Token {self.user.auth_token}",
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
                'players': ['user1']
            },
            HTTP_AUTHORIZATION=f"Token {self.user.auth_token}",
            format='json'
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response = self.client.get(
            reverse('room-detail', args=[1])
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(['user1'], response.data['players'])

    def test_user_can_not_add_random_username_at_creation_time(self):
        response = self.client.post(
            reverse('rooms'),
            data={
                'name': 'Room1',
                'players': ['random_username']
            },
            HTTP_AUTHORIZATION=f"Token {self.user.auth_token}",
            format='json'
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual('does_not_exist', response.data['players'][0].code)


class RoomJoinTestCase(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create(
            username='user1', password='p@@@@$w00rdd')
        self.user2 = User.objects.create(
            username='user2', password='p@@@@$w00rdd')
        self.user3 = User.objects.create(
            username='user3', password='p@@@@$w00rdd')
        self.user4 = User.objects.create(
            username='user4', password='p@@@@$w00rdd')
        self.user5 = User.objects.create(
            username='user5', password='p@@@@$w00rdd')
