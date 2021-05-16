from django.urls import path
from room import views

urlpatterns = [
    path('room/', views.RoomList.as_view()),
    path('room/<int:pk>/', views.RoomDetail.as_view()),
    path('room/<int:room_id>/member_list', views.RoomMemberList.as_view()),
    path('room/<int:room_id>/join_room/', views.RoomJoin.as_view()),
    path('room/<int:room_id>/leave_room/', views.RoomLeave.as_view()),
    path('room/<int:room_id>/block/<int:user_id>/', views.RoomBlock.as_view()),
    path('room/<int:room_id>/unblock/<int:user_id>/', views.RoomUnBlock.as_view()),
]