from rest_framework import serializers
from room.models import Room, RoomMember
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


class UserSerializer(serializers.ModelSerializer):
    room_members = serializers.PrimaryKeyRelatedField(many=True, queryset=RoomMember.objects.all())

    class Meta:
        model = User
        fields = ['id', 'username', 'room_members']

