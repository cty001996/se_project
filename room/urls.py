from django.urls import path
from room import views

urlpatterns = [
    path('room/', views.RoomList.as_view()),
    path('room/<int:room_id>/member_list', views.RoomMemberList.as_view()),
    path('room/<int:room_id>/join_room/', views.RoomJoin.as_view()),
    path('room_member/<int:pk>/', views.RoomMemberDetail.as_view()),
]