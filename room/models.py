from django.db import models
from django.shortcuts import reverse
TYPE_CHOICES = [('public','公開房間'), ('private','私密房間'), ('course','課程討論房間')]
CATEGORY_CHOICES = [('course', '課程討論'), ('find_group','尋求組隊')]
ACCESS_CHOICES = [('admin', '房主'), ('manager', '管理員'), ('user', '一般成員')]


class Room(models.Model):
    title = models.CharField(max_length=20)
    introduction = models.TextField(max_length=200, blank=True, default='')
    create_time = models.DateTimeField(auto_now_add=True)
    valid_time = models.DateTimeField(null=True)
    room_type = models.CharField(choices=TYPE_CHOICES, default='public', max_length=10)
    room_category = models.CharField(choices=CATEGORY_CHOICES, default='course', max_length=20)
    people_limit = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("room:detail", kwargs={"pk": self.id})

    class Meta:
        ordering = ['create_time']


class RoomMember(models.Model):
    room = models.ForeignKey(Room, related_name='members', on_delete=models.CASCADE)
    member = models.ForeignKey('auth.User', related_name='members', on_delete=models.CASCADE)
    nickname = models.CharField(max_length=20)
    access_level = models.CharField(choices=ACCESS_CHOICES, default='user', max_length=20)


