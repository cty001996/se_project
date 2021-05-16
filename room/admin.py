from django.contrib import admin
from room.models import Room, RoomMember, RoomBlock, RoomInviting, RoomRecord
# Register your models here.
admin.site.register(Room)
admin.site.register(RoomMember)
admin.site.register(RoomBlock)
admin.site.register(RoomInviting)
admin.site.register(RoomRecord)
