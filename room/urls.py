from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'room'
urlpatterns = [
    path('create', views.RoomCreate.as_view(), name='create'),
    path('index', views.RoomList.as_view(), name='list'),
    path('detail/<int:pk>', views.RoomDetail.as_view(), name='detail'),
    path('delete/<int:pk>', views.RoomDelete.as_view(), name='delete'),
    path('join_room/<int:room_id>', views.RoomJoin.as_view(), name='join_room'),
    path('api/get_member_list/<int:room_id>', views.api_get_member_list, name='api_get_member_list'),
]
