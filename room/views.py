from django.contrib.auth.models import User
from django.http import Http404
from rest_framework import status, mixins, generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from room.models import Room, RoomMember, RoomBlock
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
            # set user as admin in the room
            # RoomMemberList = {user_id}
            # RoomBlock = {}
            # update RoomDetail as the user sets it
            # update RoomRecord that this room is created
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoomDetail(APIView):

    # default handler
    def get_object(self, pk):
        try:
            return Room.objects.get(pk=pk)
        except Room.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if Room.objects.get(id=room_id).room_type == 'private' and not members.filter(member=request.user).exists():
            return error_response("You are not authorized in this private room.", status.HTTP_401_UNAUTHORIZED)
        # Here we assume course and public rooms are welcomed to be seen
        room = self.get_object(pk)
        serializer = RoomSerializer(room)
        return Response(serializer.data)

    def put(self, request, pk):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        member = RoomMember.objects.get(room_id=room_id, member=request.user)
        if not member.access_level == 'admin' and not member.access_level == 'manager':
            return error_response("You are not authorized to change settings.", status.HTTP_401_UNAUTHORIZED)
        room = self.get_object(pk)
        serializer = RoomSerializer(room, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if not RoomMember.objects.get(room_id=room_id, member=request.user).access_level == 'admin':
            return error_response("Only admin is authorized to delete room.", status.HTTP_401_UNAUTHORIZED)
        # delete RoomMemberList
        # delete RoomBlockList
        # delete Room
        # update RoomRecord that this room is deleted
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

    # In the case of creating room, it is handled in post() in class RoomList()
    def post(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return Response({"error": "Room does not exist."}, status=status.HTTP_404_NOT_FOUND)
        if RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return Response({"error": "User is already in the room."}, status=status.HTTP_400_BAD_REQUEST)
        if Room.objects.get(id=room_id).people_limit == len(RoomMember.objects.filter(room_id=room_id)):
            return Response({"error": "Room is full."}, status=status.HTTP_400_BAD_REQUEST)
        if Room.objects.get(id=room_id).room_type == 'private':
            return Response({"error": "Room is private."}, status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()
        data["access_level"] = 'user'
        serializer = RoomMemberSerializer(data=data)
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
            return Response({"error": "User is the admin, can't leave the room."}, status=status.HTTP_400_BAD_REQUEST)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoomBlockList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        blocks = RoomBlock.objects.filter(room_id=room_id)
        serializer = RoomBlockSerializer(blocks, many=True)
        return Response(serializer.data)


class RoomUserBlock(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id, user_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.objects.get(room_id=room_id, member=request.user)

        if member.access_level == 'user':
            return error_response("You don't have permission to do this action", status.HTTP_401_UNAUTHORIZED)
        if not RoomMember.object.filter(room_id=room_id, member_id=user_id).exists():
            return error_response("The target is not in the room", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.object.get(room_id=room_id, member_id=user_id)

        if member.access_level == 'admin' or member.access_level == 'manager':
            return error_response("You can't block the admin or manager", status.HTTP_401_UNAUTHORIZED)
        if user_id == request.user.id:
            return error_response("You can't block yourself", status.HTTP_400_BAD_REQUEST)

        if RoomBlock.objects.filter(room_id=room_id, blocked_user=user_id).exists():
            return error_response("The user has already been blocked", status.HTTP_400_BAD_REQUEST)

        serializer = RoomBlockSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(room=Room.objects.get(id=room_id),
                            blocked_user=User.objects.get(id=user_id),
                            block_manager=request.user)
            if RoomMember.objects.filter(room_id=room_id, member=user_id).exists():
                member = RoomMember.objects.get(room_id=room_id, member=user_id)
                member.delete()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoomUserUnBlock(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, room_id, user_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.objects.get(room_id=room_id, member=request.user)

        if member.access_level == 'user':
            return error_response("You don't have permission to do this action", status.HTTP_401_UNAUTHORIZED)

        if not RoomBlock.objects.filter(room_id=room_id, blocked_user=user_id).exists():
            return error_response("The user has not been blocked yet", status.HTTP_400_BAD_REQUEST)
        block = RoomBlock.objects.get(room_id=room_id, blocked_user=user_id)
        block.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# class RoomInvite(): for managers to invite people

# in permission.py add isManager() for authorization needs?

# class RoomRoles(): assign roles to other members (only admin is allowed to access operations:
#   assign manager: change another member to a manager
#   degrade manager: degrade a manager to a member


class RoomUserRemove(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, room_id, user_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.objects.get(room_id=room_id, member=request.user)
        if member.access_level == 'user':
            return error_response("You don't have permission to do this action", status.HTTP_401_UNAUTHORIZED)
        if not RoomMember.objects.filter(room_id=room_id, member_id=user_id).exists():
            return error_response("The user is not in the room.", status.HTTP_400_BAD_REQUEST)
        removal = RoomMember.objects.get(room_id=room_id, member_id=user_id)
        if removal.access_level == "user":
            removal.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return error_response("The user is admin or manager, can not remove", status.HTTP_401_UNAUTHORIZED)


class UserRoom(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rooms = Room.objects.filter(members__member=request.user)
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

class SetAccessLevel(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, room_id):
        if not room_exist(room_id):
            return error_response("Room does not exist", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        if not RoomMember.objects.get(room_id=room_id, member=request.user).access_level == 'admin':
            return error_response("Only admin can set access level", status.HTTP_401_UNAUTHORIZED)

        result = {}
        for key, value in request.data.items():
            if value == 'admin':
                result[key] = "error: can't set admin by this api"
                continue
            if int(key) == request.user.id:
                result[key] = "error: can't set admin itself"
                continue
            if RoomMember.objects.filter(room_id=room_id, member_id=key).exists():
                member = RoomMember.objects.get(room_id=room_id, member_id=key)
                serializer = RoomMemberSerializer(member, data={"access_level": value}, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    result[key] = value
                else:
                    result[key] = f'error: {serializer.errors}'
            else:
                result[key] = 'error: user is not in the room'

        return Response(result)


class TransferAdmin(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, room_id, user_id):
        if not room_exist(room_id):
            return error_response("Room does not exist", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        if not RoomMember.objects.get(room_id=room_id, member=request.user).access_level == 'admin':
            return error_response("Only admin can transfer admin", status.HTTP_401_UNAUTHORIZED)
        if not RoomMember.objects.filter(room_id=room_id, member_id=user_id).exists():
            return error_response("The user is not in the room", status.HTTP_400_BAD_REQUEST)

        origin_admin = RoomMember.objects.get(room_id=room_id, member=request.user)
        after_admin = RoomMember.objects.get(room_id=room_id, member_id=user_id)
        origin_admin.access_level = "manager"
        origin_admin.save()
        after_admin.access_level = "admin"
        after_admin.save()

        return Response(status=status.HTTP_200_OK)

