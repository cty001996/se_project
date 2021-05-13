from django.contrib.auth.models import User
from django.http import Http404
from rest_framework import status, mixins, generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from room.models import Room, RoomMember
from room.serializers import RoomSerializer, RoomMemberSerializer


class RoomList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rooms = Room.objects.all()
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoomMemberList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return Response({"error": "Room does not exist."}, status=status.HTTP_404_NOT_FOUND)
        members = RoomMember.objects.filter(room_id=room_id)
        if not members.filter(member=request.user).exists():
            return Response({"error": "User does not in this room."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = RoomMemberSerializer(members, many=True)
        return Response(serializer.data)


class RoomJoin(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return Response({"error": "Room does not exist."}, status=status.HTTP_404_NOT_FOUND)
        if RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return Response({"error": "User is already in the room."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = RoomMemberSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(member=request.user, room=Room.objects.get(id=room_id))
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoomMemberDetail(APIView):

    def get_object(self, pk):
        try:
            return RoomMember.objects.get(pk=pk)
        except RoomMember.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        member = self.get_object(pk)
        serializer = RoomMemberSerializer(member)
        return Response(serializer.data)

    def put(self, request, pk):
        member = self.get_object(pk)
        serializer = RoomMemberSerializer(member, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        member = self.get_object(pk)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
