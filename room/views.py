from django.http import JsonResponse
from rest_framework import status, mixins, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
import requests

from room.models import Room, RoomMember, RoomBlock, RoomInviting, RoomRecord, TYPE_CHOICES, CATEGORY_CHOICES
from room.serializers import RoomSerializer, RoomMemberSerializer, RoomBlockSerializer, RoomInvitingSerializer, \
    RoomRecordSerializer
from user.models import CustomUser, Notification


def error_response(message, status_code):
    return Response({"error": message}, status=status_code)


def room_exist(room_id):
    return Room.objects.filter(id=room_id).exists()


class RoomRecordList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        records = RoomRecord.objects.filter(room_id=room_id)
        serializer = RoomRecordSerializer(records, many=True)
        return Response(serializer.data)


class GetTypeChoices(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        response = {key: value for key, value in TYPE_CHOICES}
        return JsonResponse(response, safe=False)


class GetCategoryChoices(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        response = {key: value for key, value in CATEGORY_CHOICES}
        return JsonResponse(response, safe=False)


class RoomList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rooms = Room.objects.all()
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    def post(self, request):
        room_serializer = RoomSerializer(data=request.data)
        data = request.data.copy()
        owner = request.user
        if data.get("room_type", None) == 'course':
            data["access_level"] = "manager"
            owner = CustomUser.objects.get(username="admin")
        else:
            data["access_level"] = "admin"
        member_serializer = RoomMemberSerializer(data=data)

        if len(RoomMember.objects.filter(member=owner, access_level="admin")) >= 50:
            return error_response("room create limit has reached!", status.HTTP_400_BAD_REQUEST)
        if not room_serializer.is_valid():
            return Response(room_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if not member_serializer.is_valid():
            return Response(member_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        room_serializer.save()
        member_serializer.save(member=request.user, room=room_serializer.instance)
        if data.get("room_type", None) == 'course':
            RoomMember(room=room_serializer.instance, member=owner,
                       nickname="admin", access_level="admin").save()
        member = member_serializer.instance
        RoomRecord(room=room_serializer.instance,
                   recording=f"{member.nickname}({member.member.username}) 建立了房間!").save()
        return Response(room_serializer.data, status=status.HTTP_201_CREATED)


class RoomDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)

        room = Room.objects.get(id=room_id)
        serializer = RoomSerializer(room)
        return Response(serializer.data)

    def put(self, request, room_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.objects.get(room_id=room_id, member=request.user)
        if not member.access_level == 'admin' and not member.access_level == 'manager':
            return error_response("You are not authorized to change settings.", status.HTTP_401_UNAUTHORIZED)
        room = Room.objects.get(id=room_id)
        serializer = RoomSerializer(room, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            RoomRecord(room=room,
                       recording=f"{member.nickname}({member.member.username}) 修改了房間設定").save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, room_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        if not RoomMember.objects.get(room_id=room_id, member=request.user).access_level == 'admin':
            return error_response("Only admin is authorized to delete room.", status.HTTP_401_UNAUTHORIZED)
        # notify users that were in this room
        room = Room.objects.get(id=room_id)
        room.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoomMemberList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        members = RoomMember.objects.filter(room_id=room_id)
        serializer = RoomMemberSerializer(members, many=True)
        return Response(serializer.data)


class RoomMemberDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id, user_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member_id=user_id).exists():
            return error_response("Member does not exist.", status.HTTP_404_NOT_FOUND)
        member = RoomMember.objects.get(room_id=room_id, member_id=user_id)
        serializer = RoomMemberSerializer(member)
        return Response(serializer.data)


class RoomJoin(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # In the case of creating room, it is handled in post() in class RoomList()
    def post(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are already in the room", status.HTTP_400_BAD_REQUEST)
        if RoomBlock.objects.filter(room_id=room_id, blocked_user=request.user).exists():
            return error_response("You have been blocked by this room.", status.HTTP_401_UNAUTHORIZED)
        if Room.objects.get(id=room_id).people_limit == len(RoomMember.objects.filter(room_id=room_id)):
            return error_response("Room is full.", status.HTTP_400_BAD_REQUEST)
        if Room.objects.get(id=room_id).room_type == 'private':
            return error_response("Room is private.", status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()
        data["access_level"] = 'user'

        member_serializer = RoomMemberSerializer(data=data)
        if not member_serializer.is_valid():
            return Response(member_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        member_serializer.save(member=request.user, room=Room.objects.get(id=room_id))
        RoomRecord(room_id=room_id, recording=f"{data['nickname']}({request.user.username}) 加入了房間").save()
        response = requests.post(f'http://127.0.0.1:8090/wsServer/notify/room/{room_id}/join/',
                          {'join_userID': request.user.id})
        print(response.status_code)
        return Response(member_serializer.data, status=status.HTTP_200_OK)


class RoomLeave(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room.", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.objects.get(room_id=room_id, member=request.user)
        if member.access_level == 'admin':
            return error_response("You are admin, can't leave the room.", status.HTTP_400_BAD_REQUEST)

        RoomRecord(room=Room.objects.get(id=room_id), recording=f"{member.nickname}({member.member.username}) 離開了房間")\
            .save()
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoomBlockList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
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
        if not CustomUser.objects.filter(id=user_id).exists():
            return error_response("The target does not exist", status.HTTP_404_NOT_FOUND)
        target = CustomUser.objects.get(id=user_id)
        if user_id == request.user.id:
            return error_response("You can't block yourself", status.HTTP_400_BAD_REQUEST)
        if RoomBlock.objects.filter(room_id=room_id, blocked_user=user_id).exists():
            return error_response("The user has already been blocked", status.HTTP_400_BAD_REQUEST)

        serializer = RoomBlockSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(room=Room.objects.get(id=room_id),
                        blocked_user=CustomUser.objects.get(id=user_id),
                        block_manager=request.user)
        if RoomMember.objects.filter(room_id=room_id, member=user_id).exists():
            RoomMember.objects.get(room_id=room_id, member=user_id).delete()

        # record block and notify
        RoomRecord(room=Room.objects.get(id=room_id),
                   recording=f"{member.nickname}({member.member.username}) 封鎖了 {target.username}").save()
        Notification(user=target,
                     message=f"你被 {member.member.username} 禁止進入了房間「{Room.objects.get(id=room_id).title}」，" +
                             f"原因為:{request.data.get('reason', None)}").save()

        return Response(serializer.data, status=status.HTTP_200_OK)


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
        if not CustomUser.objects.filter(id=user_id).exists():
            return error_response("Target does not exist.", status.HTTP_404_NOT_FOUND)
        target = CustomUser.objects.get(id=user_id)
        if not RoomBlock.objects.filter(room_id=room_id, blocked_user=user_id).exists():
            return error_response("The user has not been blocked yet", status.HTTP_400_BAD_REQUEST)
        block = RoomBlock.objects.get(room_id=room_id, blocked_user=user_id)
        block.delete()

        RoomRecord(room=Room.objects.get(id=room_id),
                   recording=f"{member.nickname}({member.member.username}) 把 {target.username} 解封了").save()

        return Response(status=status.HTTP_204_NO_CONTENT)

# in permission.py add isManager() for authorization needs?


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
        if removal.access_level != "user":
            return error_response("The user is admin or manager, cannot be removed.", status.HTTP_401_UNAUTHORIZED)

        RoomRecord(room=Room.objects.get(id=room_id),
                   recording=f"{member.nickname}({member.member.username}) 踢掉了 {removal.nickname}({removal.member.username})").save()
        removal.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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

        result={}
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


class InviteUser(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id, username):
        if not CustomUser.objects.filter(username=username).exists():
            return error_response("Target user does not exist.", status.HTTP_400_BAD_REQUEST)
        user_id = CustomUser.objects.get(id=invite.room_id).id
        if not room_exist(room_id):
            return error_response("Room does not exist", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        if RoomMember.objects.get(room_id=room_id, member=request.user).access_level == 'user':
            return error_response("Only admin and manager can invite user", status.HTTP_401_UNAUTHORIZED)
        if not CustomUser.objects.filter(id=user_id).exists():
            return error_response("Target does not exist.", status.HTTP_404_NOT_FOUND)
        target = CustomUser.objects.get(id=user_id)
        if RoomMember.objects.filter(room_id=room_id, member_id=user_id).exists():
            return error_response("The user is already in the room", status.HTTP_400_BAD_REQUEST)
        if RoomBlock.objects.filter(room_id=room_id, blocked_user_id=user_id).exists():
            return error_response("The user has been blocked", status.HTTP_400_BAD_REQUEST)
        if RoomInviting.objects.filter(room_id=room_id, invited_id=user_id).exists():
            return error_response("The user has been invited", status.HTTP_400_BAD_REQUEST)

        serializer = RoomInvitingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(room=Room.objects.get(id=room_id),
                        invited=target,
                        inviter=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AcceptInviting(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invite_id):
        if not RoomInviting.objects.filter(id=invite_id, invited=request.user).exists():
            return error_response("Invite id does not exist or does not belong to you", status.HTTP_400_BAD_REQUEST)
        invite = RoomInviting.objects.get(id=invite_id, invited=request.user)
        if not room_exist(invite.room_id):
            return error_response("The room has been removed", status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data["access_level"] = 'user'
        serializer = RoomMemberSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(member=request.user, room=Room.objects.get(id=invite.room_id))
        RoomRecord(room_id=invite.room_id, recording=f"{data['nickname']}({request.user.username}) 被邀請進入了房間").save()
        invite.delete()
        return Response(serializer.data, status=status.HTTP_200_OK)


class RejectInviting(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, invite_id):
        if not RoomInviting.objects.filter(id=invite_id, invited=request.user).exists():
            return error_response("Invite id does not exist or does not belong to you", status.HTTP_400_BAD_REQUEST)
        invite = RoomInviting.objects.get(id=invite_id, invited=request.user)
        invite.delete()
        RoomRecord(room_id=invite.room_id, recording=f"{request.user.username} 拒絕了房間的邀請").save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvitationList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        invite_list = RoomInviting.objects.filter(invited=request.user)
        serializer = RoomInvitingSerializer(invite_list, many=True)
        return Response(serializer.data)


class RoomInvitationList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        if not room_exist(room_id):
            return error_response("Room does not exist", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        invite_list = RoomInviting.objects.filter(room_id=room_id)
        serializer = RoomInvitingSerializer(invite_list, many=True)
        return Response(serializer.data)


