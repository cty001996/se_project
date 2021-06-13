from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.test import TestCase
from rest_framework import status

from room.models import Room, RoomMember, RoomInviting, RoomBlock
from room.serializers import RoomSerializer, RoomInvitingSerializer, RoomBlockSerializer
from room.views import RoomList
from user.models import CustomUser


def api_client():
    user = CustomUser.objects.create_user(email='test@ntu.edu.tw', password='test', is_verify=True)
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client, user

'''
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
        response = client.  ('/room/', {'title': 'test_room', 'nickname': 'test_nickname'})
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
'''
class RoomInviteTest(TestCase):
    def setUp(self):
        self.test_room = Room.objects.create(
            title='test_room',
            people_limit=10
        )
        self.small_room = Room.objects.create(
            title='small_room',
            people_limit=1
        )
        self.test_user = CustomUser.objects.create_user(
            email='test_user@test.com',
            password='test_user'
        )
        self.test_user1 = CustomUser.objects.create_user(
            email='test1_user@test.com',
            password='test1_user'
        )

    def test_invite(self):
        client, user = api_client()
        RoomMember.objects.create(
            room=self.test_room,
            nickname='creator',
            member=user,
            access_level='admin'
        )
        response = client.post(f'/room/{self.test_room.id}/invite/{self.test_user.username}/',
                               {'room': self.test_room, 'inviter': user, 'invited': self.test_user})
        invite = RoomInviting.objects.get(room=self.test_room)
        serializer = RoomInvitingSerializer(invite)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_invite_existing_member(self):
        # inviter is the admin
        client, user = api_client()
        RoomMember.objects.create(
            room=self.test_room,
            nickname='creator',
            member=user,
            access_level='admin'
        )
        # invited is in the room
        RoomMember.objects.create(
            room=self.test_room,
            nickname='creator',
            member=self.test_user,
            access_level='user'
        )
        # invite
        response = client.post(f'/room/{self.test_room.id}/invite/{self.test_user.username}/',
                               {'room': self.test_room, 'inviter': user, 'invited': self.test_user})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        '''
    def test_invite_people_limit(self):
        # 1
        client, user = api_client()
        v = RoomMember.objects.create(
            room=self.small_room,
            nickname='creator',
            member=user,
            access_level='admin'
        )
        print('first', v.nickname)
        # invite a 3rd user
        for i in RoomMember.objects.filter(id=self.small_room.id):
            print(i.nickname)
        response = client.post(f'/room/{self.small_room.id}/invite/{self.test_user1.username}/',
                               {'room': self.small_room, 'inviter': user, 'invited': self.test_user1})
        print('invited on the list: ', RoomInviting.objects.get(room=self.small_room).invited)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

'''
class BlockTest(TestCase):
    def setUp(self):
        self.test_room = Room.objects.create(
            title='test_room',
            people_limit=10
        )
        self.test_user = CustomUser.objects.create_user(
            email='test_user@test.com',
            password='test_user'
        )
        self.blocked = CustomUser.objects.create_user(
            email='blocked@test.com',
            password='blocked'
        )
        RoomMember.objects.create(
            room=self.test_room,
            nickname='mod',
            member=self.test_user,
            access_level='user'
        )
        RoomBlock.objects.create(
            room = self.test_room,
            blocked_user = self.blocked,
            reason = "spam",
            block_manager = self.test_user
        )

    def test_block_user(self):
        client, user = api_client()
        RoomMember.objects.create(
            room=self.test_room,
            nickname='creator',
            member=user,
            access_level='admin'
        )
        response = client.post(f'/room/{self.test_room.id}/block/{self.test_user.id}/',
                               {'room': self.test_room, 'block_manager': user, 'blocked_user': self.test_user,
                                'reason': "spam1"})
        block = RoomBlock.objects.get(reason='spam1')
        serializer = RoomBlockSerializer(block)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_block_again(self):
        client, user = api_client()
        RoomMember.objects.create(
            room=self.test_room,
            nickname='creator',
            member=user,
            access_level='admin'
        )
        response = client.post(f'/room/{self.test_room.id}/block/{self.blocked.id}/',
                               {'room': self.test_room, 'block_manager': user, 'blocked_user': self.blocked,
                                'reason': "spam"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class TransferAdminTest(TestCase):
    def setUp(self):
        self.test_room = Room.objects.create(
            title='test_room',
            people_limit=10
        )
        self.test_user = CustomUser.objects.create_user(
            email='test_user@test.com',
            password='test_user'
        )
        RoomMember.objects.create(
            room=self.test_room,
            nickname='normal_user',
            member=self.test_user,
            access_level='user'
        )
    def test_transfer_admin(self):
        client, user = api_client()
        RoomMember.objects.create(
            room=self.test_room,
            nickname='creator',
            member=user,
            access_level='admin'
        )

        # have bugs, incomplete
        response = client.put(f'room/{self.test_room.id}/transfer_admin/{user.id}/')
        print(response.status_code)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

