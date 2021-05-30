from django.urls import path
from room import views

urlpatterns = [
    path('room_record/<int:room_id>/', views.RoomRecordList.as_view()),
    path('room/', views.RoomList.as_view()),
    path('room/<int:room_id>/', views.RoomDetail.as_view()),
    path('room/<int:room_id>/member_list', views.RoomMemberList.as_view()),
    path('room/<int:room_id>/member/<int:user_id>/', views.RoomMemberDetail.as_view()),
    path('room/<int:room_id>/join_room/', views.RoomJoin.as_view()),
    path('room/<int:room_id>/leave_room/', views.RoomLeave.as_view()),
    path('room/<int:room_id>/block_list/', views.RoomBlockList.as_view()),
    path('room/<int:room_id>/block/<int:user_id>/', views.RoomUserBlock.as_view()),
    path('room/<int:room_id>/unblock/<int:user_id>/', views.RoomUserUnBlock.as_view()),
    path('room/<int:room_id>/remove/<int:user_id>/', views.RoomUserRemove.as_view()),
    path('user_room/', views.UserRoom.as_view()),
    path('room/<int:room_id>/set_access_level/', views.SetAccessLevel.as_view()),
    path('room/<int:room_id>/transfer_admin/<int:user_id>/', views.TransferAdmin.as_view()),
    path('room/<int:room_id>/invite/<int:user_id>/', views.InviteUser.as_view()),
    path('accept_invite/<int:invite_id>/', views.AcceptInviting.as_view()),
    path('reject_invite/<int:invite_id>/', views.RejectInviting.as_view()),
    path('invitation/', views.InvitationList.as_view()),
    path('room/<int:room_id>/invitation/', views.RoomInvitationList.as_view()),
]