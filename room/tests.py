from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate

from django.test import TestCase
from rest_framework import status

from room.models import Room
from room.serializers import RoomSerializer
from room.views import RoomList
from user.models import CustomUser


class GetAllRoomTest(TestCase):

    def setUp(self):
        Room.objects.create(
            title='test_room1')
        Room.objects.create(
            title='test_room2')

    def test_get_all_rooms(self):
        factory = APIRequestFactory()
        request = factory.get('/room/')

        user = CustomUser.objects.get(username='test1')
        force_authenticate(request, user=user, token=user.auth_token)
        view = RoomList.as_view()
        response = view(request)
        rooms = Room.objects.all()
        serializer = RoomSerializer(rooms, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
