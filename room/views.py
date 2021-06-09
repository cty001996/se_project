from django.http import JsonResponse
from rest_framework import status, mixins, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
import requests

from room.models import Room, RoomMember, RoomBlock, RoomInviting, RoomRecord, TYPE_CHOICES, \
    CATEGORY_CHOICES, CATEGORY_IMAGE_URL
from room.serializers import RoomSerializer, RoomMemberSerializer, RoomBlockSerializer, RoomInvitingSerializer, \
    RoomRecordSerializer
from user.models import CustomUser, Notification

from user.permissions import IsVerify


def error_response(message, status_code):
    return Response({"error": message}, status=status_code)


def room_exist(room_id):
    return Room.objects.filter(id=room_id).exists()


def ws_update_room(room_id, update_string):
    response = requests.post(
        f'https://ntu-online-group-ws.herokuapp.com/wsServer/notify/room/{room_id}/update/',
        {'update_data': update_string}
    )
    print(response.content)


def ws_join_room(room_id, user_id):
    response = requests.post(
        f'https://ntu-online-group-ws.herokuapp.com/wsServer/notify/room/{room_id}/join/',
        {'join_userID': user_id}
    )
    print(response.content)


def ws_leave_room(room_id, user_id):
    response = requests.post(
        f'https://ntu-online-group-ws.herokuapp.com/wsServer/notify/room/{room_id}/remove/',
        {'removed_userID': user_id}
    )
    print(response.content)


def add_notification(user, notify_string):
    Notification(user=user,
                 message=notify_string).save()
    response = requests.post(
        f'https://ntu-online-group-ws.herokuapp.com/wsServer/notify/user/{user.id}/',
    )
    print(response.content)


class RoomRecordList(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def get(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
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
        response = []
        for key, value in CATEGORY_CHOICES:
            content = {
                "value": key,
                "url": CATEGORY_IMAGE_URL[key],
                "category": value,
            }
            response.append(content)
        return JsonResponse(response, safe=False)


class RoomList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rooms = Room.objects.all()
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_verify:
            return error_response("You do not have the right to create a room", status.HTTP_403_FORBIDDEN)
        room_serializer = RoomSerializer(data=request.data)
        data = request.data.copy()
        data["access_level"] = "admin"
        member_serializer = RoomMemberSerializer(data=data)

        if len(RoomMember.objects.filter(member=request.user, access_level="admin")) >= 50:
            return error_response("房間已到人數上限！", status.HTTP_400_BAD_REQUEST)
        if not room_serializer.is_valid():
            return Response(room_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if not member_serializer.is_valid():
            return Response(member_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        room_serializer.save()
        room = room_serializer.instance
        member_serializer.save(member=request.user, room=room_serializer.instance)

        member = member_serializer.instance
        RoomRecord(room=room,
                   recording=f"{member.nickname}({member.member.username}) 建立了房間!").save()
        return Response(room_serializer.data, status=status.HTTP_201_CREATED)


class RoomDetail(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def get(self, request, room_id):
        if not room_exist(room_id):
            return error_response("房間不存在", status.HTTP_404_NOT_FOUND)

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
            return error_response("You are not authorized to change settings.", status.HTTP_403_FORBIDDEN)
        room = Room.objects.get(id=room_id)
        serializer = RoomSerializer(room, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            RoomRecord(room=room,
                       recording=f"{member.nickname}({member.member.username}) 修改了房間設定").save()
            ws_update_room(room_id, 'profile')
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, room_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        if not RoomMember.objects.get(room_id=room_id, member=request.user).access_level == 'admin':
            return error_response("Only admin is authorized to delete room.", status.HTTP_403_FORBIDDEN)
        if Room.objects.get(id=room_id).room_type == 'course':
            return error_response("課程討論房間無法被刪除！", status.HTTP_400_BAD_REQUEST)

        for in_member in RoomMember.objects.filter(room_id=room_id):
            add_notification(in_member.member, f"房間「{Room.objects.get(id=room_id).title}」被房主刪除了。")
        room = Room.objects.get(id=room_id)
        room.delete()
        ws_update_room(room_id, 'delete_room')
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoomMemberList(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def get(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        members = RoomMember.objects.filter(room_id=room_id)
        serializer = RoomMemberSerializer(members, many=True)
        return Response(serializer.data)


class RoomMemberDetail(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def get(self, request, room_id, user_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member_id=user_id).exists():
            return error_response("Member does not exist.", status.HTTP_404_NOT_FOUND)
        member = RoomMember.objects.get(room_id=room_id, member_id=user_id)
        serializer = RoomMemberSerializer(member)
        return Response(serializer.data)


class RoomJoin(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def post(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return error_response("房間不存在", status.HTTP_404_NOT_FOUND)
        if RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are already in the room", status.HTTP_400_BAD_REQUEST)
        if RoomBlock.objects.filter(room_id=room_id, blocked_user=request.user).exists():
            return error_response("你被此房間封鎖了，無法進入", status.HTTP_403_FORBIDDEN)
        if Room.objects.get(id=room_id).people_limit == len(RoomMember.objects.filter(room_id=room_id)):
            return error_response("房間已滿，無法進入", status.HTTP_400_BAD_REQUEST)
        if Room.objects.get(id=room_id).room_type == 'private':
            return error_response("此為私人房間，無法直接進入", status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data["access_level"] = 'user'

        member_serializer = RoomMemberSerializer(data=data)
        if not member_serializer.is_valid():
            return Response(member_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        member_serializer.save(member=request.user, room=Room.objects.get(id=room_id))
        RoomRecord(room_id=room_id, recording=f"{data['nickname']}({request.user.username}) 加入了房間").save()
        ws_update_room(room_id, 'member_list')
        return Response(member_serializer.data, status=status.HTTP_200_OK)


class RoomLeave(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def delete(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room.", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.objects.get(room_id=room_id, member=request.user)
        if member.access_level == 'admin':
            return error_response("你是房主，無法離開房間", status.HTTP_400_BAD_REQUEST)

        RoomRecord(room=Room.objects.get(id=room_id),
                   recording=f"{member.nickname}({member.member.username}) 離開了房間").save()
        ws_leave_room(room_id, request.user.id)
        ws_update_room(room_id, 'member_list')
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoomBlockList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        if not Room.objects.filter(id=room_id).exists():
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        blocks = RoomBlock.objects.filter(room_id=room_id)
        serializer = RoomBlockSerializer(blocks, many=True)
        return Response(serializer.data)


class RoomUserBlock(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def post(self, request, room_id, user_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.objects.get(room_id=room_id, member=request.user)

        if member.access_level == 'user':
            return error_response("You don't have permission to do this action", status.HTTP_403_FORBIDDEN)
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
            ws_leave_room(room_id, target.id)
            ws_update_room(room_id, 'member_list')


        RoomRecord(room=Room.objects.get(id=room_id),
                   recording=f"{member.nickname}({member.member.username}) 封鎖了 {target.username}").save()
        add_notification(target,
                         f"你被 {member.member.username} 禁止進入了房間「{Room.objects.get(id=room_id).title}」，" +
                         f"原因為:{request.data.get('reason', None)}")
        ws_update_room(room_id, 'block_list')

        return Response(serializer.data, status=status.HTTP_200_OK)


class RoomUserUnBlock(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def delete(self, request, room_id, user_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.objects.get(room_id=room_id, member=request.user)
        if member.access_level == 'user':
            return error_response("You don't have permission to do this action", status.HTTP_403_FORBIDDEN)
        if not CustomUser.objects.filter(id=user_id).exists():
            return error_response("Target does not exist.", status.HTTP_404_NOT_FOUND)
        target = CustomUser.objects.get(id=user_id)
        if not RoomBlock.objects.filter(room_id=room_id, blocked_user=user_id).exists():
            return error_response("The user has not been blocked yet", status.HTTP_400_BAD_REQUEST)
        block = RoomBlock.objects.get(room_id=room_id, blocked_user=user_id)
        block.delete()

        RoomRecord(room=Room.objects.get(id=room_id),
                   recording=f"{member.nickname}({member.member.username}) 把 {target.username} 解封了").save()

        add_notification(target, f"{member.member.username} 將你從房間「{Room.objects.get(id=room_id).title}」解封了")
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoomUserRemove(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def delete(self, request, room_id, user_id):
        if not room_exist(room_id):
            return error_response("Room does not exist.", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        member = RoomMember.objects.get(room_id=room_id, member=request.user)
        if member.access_level == 'user':
            return error_response("You don't have permission to do this action", status.HTTP_403_FORBIDDEN)
        if not RoomMember.objects.filter(room_id=room_id, member_id=user_id).exists():
            return error_response("The user is not in the room.", status.HTTP_400_BAD_REQUEST)
        removal = RoomMember.objects.get(room_id=room_id, member_id=user_id)
        if removal.access_level == "admin":
            return error_response("房主無法被踢出房間", status.HTTP_403_FORBIDDEN)

        RoomRecord(room=Room.objects.get(id=room_id),
                   recording=f"{member.nickname}({member.member.username}) 踢掉了 {removal.nickname}({removal.member.username})").save()
        add_notification(removal.member,
                         f"你被 {member.member.username} 踢出了了房間「{Room.objects.get(id=room_id).title}」")
        removal.delete()
        ws_leave_room(room_id, user_id)
        ws_update_room(room_id, 'member_list')
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserRoom(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rooms = Room.objects.filter(members__member=request.user)
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)


class UserAdminRoom(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rooms = Room.objects.filter(members__member=request.user, members__access_level='admin')
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)


class SetAccessLevel(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def put(self, request, room_id):
        if not room_exist(room_id):
            return error_response("Room does not exist", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        if not RoomMember.objects.get(room_id=room_id, member=request.user).access_level == 'admin':
            return error_response("Only admin can set access level", status.HTTP_403_FORBIDDEN)

        result={}
        for key, value in request.data.items():
            if value == 'admin':
                result[key] = "error: can't set admin by this api"
                continue
            if int(key) == request.user.id:
                result[key] = "無法在此設定房主的權限，請使用轉移房主功能"
                continue
            if RoomMember.objects.filter(room_id=room_id, member_id=key).exists():
                member = RoomMember.objects.get(room_id=room_id, member_id=key)
                serializer = RoomMemberSerializer(member, data={"access_level": value}, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    result[key] = value
                    if value == 'user':
                        add_notification(member.member,
                                         f"你被「{Room.objects.get(id=room_id).title}」的房主設置為一般使用者。")
                    elif value == 'manager':
                        add_notification(member.member,
                                         f"你被「{Room.objects.get(id=room_id).title}」的房主設置為管理者。")
                else:
                    result[key] = f'error: {serializer.errors}'
            else:
                result[key] = 'error: user is not in the room'
        ws_update_room(room_id, 'member_list')
        return Response(result)


class TransferAdmin(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def put(self, request, room_id, user_id):
        if not room_exist(room_id):
            return error_response("Room does not exist", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        if not RoomMember.objects.get(room_id=room_id, member=request.user).access_level == 'admin':
            return error_response("Only admin can transfer admin", status.HTTP_403_FORBIDDEN)
        if not RoomMember.objects.filter(room_id=room_id, member_id=user_id).exists():
            return error_response("The user is not in the room", status.HTTP_400_BAD_REQUEST)

        origin_admin = RoomMember.objects.get(room_id=room_id, member=request.user)
        after_admin = RoomMember.objects.get(room_id=room_id, member_id=user_id)
        origin_admin.access_level = "manager"
        origin_admin.save()
        after_admin.access_level = "admin"
        after_admin.save()

        RoomRecord(room=Room.objects.get(id=room_id),
                   recording=f"{after_admin.nickname}({after_admin.member.username})被升為房主").save()
        ws_update_room(room_id, 'member_list')
        add_notification(after_admin.member,
                         f"你被升為「{Room.objects.get(id=room_id).title}」的房主")
        return Response(status=status.HTTP_200_OK)


class InviteUser(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def post(self, request, room_id, username):
        if not CustomUser.objects.filter(username=username).exists():
            return error_response("使用者不存在", status.HTTP_400_BAD_REQUEST)
        target = CustomUser.objects.get(username=username)
        user_id = target.id
        if not room_exist(room_id):
            return error_response("Room does not exist", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        if RoomMember.objects.get(room_id=room_id, member=request.user).access_level == 'user':
            return error_response("Only admin and manager can invite user", status.HTTP_403_FORBIDDEN)
        if RoomMember.objects.filter(room_id=room_id, member_id=user_id).exists():
            return error_response("使用者已在房內", status.HTTP_400_BAD_REQUEST)
        if RoomBlock.objects.filter(room_id=room_id, blocked_user_id=user_id).exists():
            return error_response("使用者被封鎖了，無法邀請", status.HTTP_400_BAD_REQUEST)
        if RoomInviting.objects.filter(room_id=room_id, invited_id=user_id).exists():
            return error_response("使用者已被邀請", status.HTTP_400_BAD_REQUEST)

        serializer = RoomInvitingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(room=Room.objects.get(id=room_id),
                        invited=target,
                        inviter=request.user)

        member = RoomMember.objects.get(room_id=room_id, member=request.user)
        RoomRecord(room=Room.objects.get(id=room_id),
                   recording=f"{member.nickname}({request.user.username}) 邀請了 {target.username} 進入房間").save()
        ws_update_room(room_id, 'invite_list')
        add_notification(target,
                         f"你被邀請進入房間:「{Room.objects.get(id=room_id).title}」")
        return Response(serializer.data, status=status.HTTP_200_OK)


class AcceptInviting(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

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
        RoomRecord(room_id=invite.room_id, recording=f"{data['nickname']}({request.user.username}) 同意了邀請進入了房間").save()
        ws_update_room(invite.room_id, 'member_list,invite_list')
        invite.delete()
        return Response(serializer.data, status=status.HTTP_200_OK)


class RejectInviting(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def delete(self, request, invite_id):
        if not RoomInviting.objects.filter(id=invite_id, invited=request.user).exists():
            return error_response("Invite id does not exist or does not belong to you", status.HTTP_400_BAD_REQUEST)
        invite = RoomInviting.objects.get(id=invite_id, invited=request.user)
        invite.delete()
        RoomRecord(room_id=invite.room_id, recording=f"{request.user.username} 拒絕了房間的邀請").save()
        ws_update_room(invite.room_id, 'invite_list')
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvitationList(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def get(self, request):
        invite_list = RoomInviting.objects.filter(invited=request.user)
        serializer = RoomInvitingSerializer(invite_list, many=True)
        return Response(serializer.data)


class RoomInvitationList(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def get(self, request, room_id):
        if not room_exist(room_id):
            return error_response("Room does not exist", status.HTTP_404_NOT_FOUND)
        if not RoomMember.objects.filter(room_id=room_id, member=request.user).exists():
            return error_response("You are not in the room", status.HTTP_400_BAD_REQUEST)
        invite_list = RoomInviting.objects.filter(room_id=room_id)
        serializer = RoomInvitingSerializer(invite_list, many=True)
        return Response(serializer.data)
