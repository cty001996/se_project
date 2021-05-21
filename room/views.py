from django.contrib.auth.models import User
from django.http import Http404
from rest_framework import status, mixins, generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from room.models import Room, RoomMember
from room.serializers import RoomSerializer, RoomMemberSerializer, RoomBlockSerializer


def error_response(message, status_code):
    return Response({"error": message}, status=status_code)


def room_exist(room_id):
    return Room.objects.filter(id=room_id).exists()


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
    # would post() automatically update RoomDetail, RoomMemberList, RoomBlock?


class RoomDetail(APIView):

    # default handler
    def get_object(self, pk):
        try:
            return Room.objects.get(pk=pk)
        except Room.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        # should return partial data, based on the room type
        # public: all data, private: minimum data (for anyone), all data (for member) ...
        room = self.get_object(pk)
        serializer = RoomSerializer(room)
        return Response(serializer.data)

    def put(self, request, pk):
        # should return partial data, based on the room type
        # public: all data, private: minimum data (for anyone), all data (for managers) ...
        room = self.get_object(pk)
        serializer = RoomSerializer(room, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # must be admin level to delete the room
        # should first go to RoomList to delete?
        room = self.get_object(pk)
        room.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoomMemberList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return Response({"error": "Room does not exist."}, status=status.HTTP_404_NOT_FOUND)
        members = RoomMember.objects.filter(room_id=room_id)
        if not members.filter(member=request.user).exists():
            return Response({"error": "User is not in this room."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = RoomMemberSerializer(members, many=True)
        return Response(serializer.data)

    # def put() for updates in RoomJoin


class RoomJoin(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return Response({"error": "Room does not exist."}, status=status.HTTP_404_NOT_FOUND)
        if RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return Response({"error": "User is already in the room."}, status=status.HTTP_400_BAD_REQUEST)
        if Room.objects.get(id=room_id).people_limit == len(RoomMember.objects.filter(room_id=room_id)):
            return Response({"error": "Room is full."}, status=status.HTTP_400_BAD_REQUEST)
        if Room.objects.get(id=room_id).room_type == 'private':
            return Response({"error": "Room is private."}, status=status.HTTP_401_UNAUTHORIZED)

        request.data["access_level"] = 'user'
        serializer = RoomMemberSerializer(data=request.data)
        if serializer.is_valid():

            serializer.save(member=request.user, room=Room.objects.get(id=room_id))
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoomLeave(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return Response({"error": "Room does not exist."}, status=status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return Response({"error": "User is not in the room."}, status=status.HTTP_400_BAD_REQUEST)

        member = RoomMember.objects.get(room_id=room_id, member=request.user)
        if member.access_level == 'admin':
            return Response({"error": "User is admin, can't leave the room."}, status=status.HTTP_400_BAD_REQUEST)
        # Should we remind the admin to either assign other admin, or to delete the room?
        # can admin assign another manager / member as the admin? see the final few lines
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoomBlock(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id, user_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if member.access_level == 'user':
            return error_response("User doesn't have the permission to do this action.", status.HTTP_401_UNAUTHORIZED)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("User is not in the room.", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.objects.get(room_id=room_id, member=request.user)
        if not RoomMember.objects.filter(room_id=room_id, member=user_id).exists():
            return error_response("Blocked_user is not in this room.", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.objects.get(room_id=room_id, member=user_id)
        if member.access_level == 'admin' or member.access_level == 'manager':
            return error_response("Cannot block the admin or a manager", status.HTTP_401_UNAUTHORIZED)
        if user_id == request.user.id:
            return error_response("Users cannot block themself.", status.HTTP_400_BAD_REQUEST)
        if RoomBlock.objects.filter(room_id=room_id, blocked_user=user_id).exists():
            return error_response("The user has been blocked.", status.HTTP_400_BAD_REQUEST)


        serializer = RoomBlockSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(room=Room.objects.get(id=room_id),
                            blocked_user=User.objects.get(id=user_id),
                            block_manager=request.user)
            member.delete()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    '''
        def get(self, request, room_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists(): # if not member
            return error_response("User doesn't have the permission to do this action.", status.HTTP_401_UNAUTHORIZED)
        if not RoomMember.objects.filter(room_id=room_id, member=user_id).exists():
            return error_response("Blocked_user is not in this room.", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.objects.get(room_id=room_id, member=user_id)

        # Response the data
       
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    '''


class RoomUnBlock(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, room_id, user_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if member.access_level == 'user':
            return error_response("User doesn't have permission to do this action.", status.HTTP_401_UNAUTHORIZED)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("User is not in the room.", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.objects.get(room_id=room_id, member=request.user)
        if not RoomBlock.objects.filter(room_id=room_id, blocked_user=user_id).exists():
            return error_response("User has not been blocked yet.", status.HTTP_400_BAD_REQUEST)
        block = RoomBlock.objects.get(room_id=room_id, blocked_user=user_id)
        block.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# class RoomInvite(): for managers to invite people

# in permission.py add isManager() for authorization needs?

# class RoomRoles(): assign roles to other members (only admin is allowed to access operations:
# assign admin: change another member to admin (the original admin will degrade to manager?)
# assign manager: change another member to a manager
# degrade manager: degrade a manager to a member
