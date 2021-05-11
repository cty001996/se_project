from django.shortcuts import render, reverse, get_object_or_404
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.views import generic
from room.models import Room, RoomMember
from room.serializers import RoomSerializer

from rest_framework import viewsets


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


def api_get_member_list(request, room_id):
    origin_member_list = RoomMember.objects.filter(room__id=room_id).order_by('access_level')
    member_list = [{"nickname":member.nickname,
                    "access_level":member.get_access_level_display()}
                   for member in origin_member_list]
    return JsonResponse(member_list, safe=False, json_dumps_params={'ensure_ascii':False})

