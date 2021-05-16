from rest_framework import serializers
from room.models import Room, RoomMember, RoomBlock, RoomInviting, RoomRecord
from django.contrib.auth.models import User


class RoomSerializer(serializers.ModelSerializer):
    #members = serializers.PrimaryKeyRelatedField(many=True, queryset=RoomMember.objects.all())

    class Meta:
        model = Room
        fields = '__all__'


class RoomMemberSerializer(serializers.ModelSerializer):
    room_id = serializers.ReadOnlyField(source='room.id')
    member_id = serializers.ReadOnlyField(source='member.id')

    class Meta:
        model = RoomMember
        fields = ['room_id', 'member_id', 'nickname', 'access_level']


class RoomBlockSerializer(serializers.ModelSerializer):
    room_id = serializers.ReadOnlyField(source='room.id')
    blocked_user_id = serializers.ReadOnlyField(source='blocked_user.id')
    block_manager_id = serializers.ReadOnlyField(source='block_manager.id')

    class Meta:
        model = RoomBlock
        fields = ['room_id', 'blocked_user_id', 'block_manager_id', 'reason']


class RoomInvitingSerializer(serializers.ModelSerializer):
    room_id = serializers.ReadOnlyField(source='room.id')
    inviter_id = serializers.ReadOnlyField(source='inviter.id')
    invited_id = serializers.ReadOnlyField(source='invited.id')

    class Meta:
        model = RoomInviting
        fields = '__all__'


class RoomRecordSerializer(serializers.ModelSerializer):
    room_id = serializers.ReadOnlyField(source='room.id')

    class Meta:
        model = RoomRecord
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    room_members = serializers.PrimaryKeyRelatedField(many=True, queryset=RoomMember.objects.all())

    class Meta:
        model = User
        fields = ['id', 'username', 'room_members']

