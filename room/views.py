from django.shortcuts import render, reverse, get_object_or_404
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.views import generic
from .models import Room, RoomMember


class RoomCreate(generic.CreateView):
    # form_class = RoomModelForm
    model = Room
    fields=['title', 'introduction','room_type','room_category', 'people_limit']
    template_name = 'room/create.html'

class RoomDelete(generic.DeleteView):
    model = Room
    template_name = 'room/delete.html'
    success_url = reverse_lazy("room:list")

class RoomList(generic.ListView):
    template_name = 'room/index.html'
    context_object_name = 'room_list'

    def get_queryset(self):
        return Room.objects.all()

class RoomDetail(generic.DetailView):
    model = Room
    template_name = 'room/detail.html'

class RoomJoin(generic.CreateView):
    model = RoomMember
    fields = ['nickname']
    template_name = 'room/join_room.html'

    def form_valid(self, form):
        form.instance.room = get_object_or_404(Room, id=self.kwargs['room_id'])
        return super(RoomJoin, self).form_valid(form)

    def get_success_url(self):
        return reverse("room:detail", kwargs={"pk": self.kwargs['room_id']})

def api_get_member_list(request, room_id):
    origin_member_list = RoomMember.objects.filter(room__id=room_id).order_by('access_level')
    member_list = [{"nickname":member.nickname,
                    "access_level":member.get_access_level_display()}
                   for member in origin_member_list]
    return JsonResponse(member_list, safe=False, json_dumps_params={'ensure_ascii':False})

