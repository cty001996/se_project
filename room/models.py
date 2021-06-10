from django.conf import settings
from django.db import models
from django.shortcuts import reverse

TYPE_CHOICES = [('public', '公開房間'), ('private', '私密房間'), ('course', '課程討論房間')]
CATEGORY_CHOICES = [
    ('course', '課程討論'),
    ('eating', '吃飯'),
    ('hiking', '爬山')
]
CATEGORY_IMAGE_URL = {
    'course': 'https://i.imgur.com/GIiSOLM.jpg',
    'eating': 'https://i.imgur.com/kN4J0UL.jpg',
    'hiking': 'https://i.imgur.com/17SSeJb.png',
}
ACCESS_CHOICES = [('admin', '房主'), ('manager', '管理員'), ('user', '一般成員')]


class Room(models.Model):
    title = models.CharField(max_length=20, unique=True)
    introduction = models.TextField(max_length=200, blank=True, default='')
    create_time = models.DateTimeField(auto_now_add=True)
    valid_time = models.DateTimeField(null=True)
    room_type = models.CharField(choices=TYPE_CHOICES, default='public', max_length=10)
    room_category = models.CharField(choices=CATEGORY_CHOICES, default='course', max_length=20)
    people_limit = models.IntegerField(default=0)
    image_url = models.URLField(default="")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['create_time']


class RoomMember(models.Model):
    room = models.ForeignKey(Room, related_name='members', on_delete=models.CASCADE)
    member = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='members', on_delete=models.CASCADE)
    nickname = models.CharField(max_length=20)
    access_level = models.CharField(choices=ACCESS_CHOICES, default='user', max_length=20)



class RoomBlock(models.Model):
    room = models.ForeignKey(Room, related_name='block_list', on_delete=models.CASCADE)
    blocked_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='be_blocked_list', on_delete=models.CASCADE)
    block_time = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=50)
    block_manager = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='block_list', on_delete=models.CASCADE)



class RoomInviting(models.Model):
    room = models.ForeignKey(Room, related_name='invite_list', on_delete=models.CASCADE)
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='inviter_list', on_delete=models.CASCADE)
    invite_time = models.DateTimeField(auto_now_add=True)
    invited = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='invited_list', on_delete=models.CASCADE)
    #status = models.CharField(choices=INVITE_CHOICES, default='open', max_length=10)



class RoomInvitingRequest(models.Model):
    room = models.ForeignKey(Room, related_name='invite_request_list', on_delete=models.CASCADE)
    request_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='request_user_list', on_delete=models.CASCADE)
    request_time = models.DateTimeField(auto_now_add=True)
    #status = models.CharField(choices=INVITE_CHOICES, default='open', max_length=10)



class RoomRecord(models.Model):
    room = models.ForeignKey(Room, related_name='records', on_delete=models.CASCADE)
    record_time = models.DateTimeField(auto_now_add=True)
    recording = models.CharField(max_length=100)
    # record actions: create, join, leave, block, unblock, remove


class RoomMessage(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(max_length=500)
    nickname = models.CharField(max_length=100)
    recv_time = models.DateTimeField(auto_now_add=True)

