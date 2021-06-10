from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.test import TestCase
from rest_framework import status

from room.models import Room, RoomMember
from room.serializers import RoomSerializer
from room.views import RoomList
from user.models import CustomUser


def api_client():
    user = CustomUser.objects.create_user(email='test@ntu.edu.tw', password='test', is_verify=True)
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client, user


class GetAllRoomTest(TestCase):
    def setUp(self):
        Room.objects.create(
            title='test_room1')
        Room.objects.create(
            title='test_room2')

    def test_get_all_rooms(self):
        client, user = api_client()
        response = client.get('/room/')
        rooms = Room.objects.all()
        serializer = RoomSerializer(rooms, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RoomCreateTest(TestCase):
    def setUp(self):
        Room.objects.create(
            title='same_title'
        )

    def test_create_room(self):
        client, user = api_client()
        response = client.post('/room/', {'title': 'test_room', 'nickname': 'test_nickname'})
        room = Room.objects.get(title='test_room')
        serializer = RoomSerializer(room)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, serializer.data)
        members = RoomMember.objects.filter(room_id=room.id)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].nickname, 'test_nickname')
        self.assertEqual(members[0].access_level, 'admin')

    def test_create_room_with_same_title(self):
        client, user = api_client()
        response = client.post('/room/', {'title': 'same_title', 'nickname': 'test_nickname'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RoomJoinTest(TestCase):
    def setUp(self):
        self.test_room = Room.objects.create(
            title='test_room',
            people_limit=10,
        )
        self.private_room = Room.objects.create(
            title='private_room',
            room_type='private',
        )
        self.another_user = CustomUser.objects.create_user(
            email='another@test.com',
            password='test'
        )
        self.test_member = RoomMember.objects.create(
            room=self.test_room,
            nickname='same_nickname',
            member=self.another_user
        )

    def test_room_join(self):
        client, user = api_client()
        response = client.post(f'/room/{self.test_room.id}/join_room/', {'nickname': 'test_nickname'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        member = RoomMember.objects.get(room_id=self.test_room.id, nickname='test_nickname')
        self.assertEqual(member.access_level, 'user')

    def test_room_join_with_same_nickname(self):
        client, user = api_client()
        response = client.post(f'/room/{self.test_room.id}/join_room/', {'nickname': 'same_nickname'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_join_private_room(self):
        client, user = api_client()
        response = client.post(f'/room/{self.private_room.id}/join_room/', {'nickname': 'test_nickname'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RoomLeaveTest(TestCase):
    def setUp(self):
        self.test_room = Room.objects.create(
            title='test_room'
        )

    def test_room_leave(self):
        client, user = api_client()
        test_member = RoomMember.objects.create(
            room=self.test_room,
            nickname='test_nickname',
            member=user
        )
        response = client.delete(f'/room/{self.test_room.id}/leave_room/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        members = RoomMember.objects.filter(room_id=self.test_room.id, member=user)
        self.assertEqual(len(members), 0)






