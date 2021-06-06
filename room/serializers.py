from rest_framework import serializers
from room.models import Room, RoomMember, RoomBlock, RoomInviting, RoomRecord
from django.contrib.auth.models import User


class RoomSerializer(serializers.ModelSerializer):

    class Meta:
        model = Room
        fields = '__all__'


class RoomMemberSerializer(serializers.ModelSerializer):
    room_id = serializers.ReadOnlyField(source='room.id')
    member_id = serializers.ReadOnlyField(source='member.id')
    username = serializers.ReadOnlyField(source='member.username')

    class Meta:
        model = RoomMember
        fields = ['room_id', 'member_id', 'nickname', 'access_level', 'username']


class RoomBlockSerializer(serializers.ModelSerializer):
    room_id = serializers.ReadOnlyField(source='room.id')
    blocked_user_id = serializers.ReadOnlyField(source='blocked_user.id')
    block_manager_id = serializers.ReadOnlyField(source='block_manager.id')
    username = serializers.ReadOnlyField(source='member.username')

    class Meta:
        model = RoomBlock
        fields = ['room_id', 'blocked_user_id', 'block_manager_id', 'reason', 'username']


class RoomInvitingSerializer(serializers.ModelSerializer):
    room_id = serializers.ReadOnlyField(source='room.id')
    inviter_id = serializers.ReadOnlyField(source='inviter.id')
    invited_id = serializers.ReadOnlyField(source='invited.id')
    inviter_username = serializers.ReadOnlyField(source='inviter.username')
    invited_username = serializers.ReadOnlyField(source='invitee.username')

    class Meta:
        model = RoomInviting
        fields = ['id', 'room_id', 'inviter_id', 'invited_id', 'inviter_username', 'invited_username'] # no invite status


class RoomRecordSerializer(serializers.ModelSerializer):
    room_id = serializers.ReadOnlyField(source='room.id')

    class Meta:
        model = RoomRecord
        fields = ('room_id', 'record_time', 'recording')


class UserSerializer(serializers.ModelSerializer):
    room_members = serializers.PrimaryKeyRelatedField(many=True, queryset=RoomMember.objects.all())

    class Meta:
        model = User
        fields = ['id', 'username', 'room_members']

