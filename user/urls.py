from django.urls import path
from user import views

urlpatterns = [
    path('register/', views.Register.as_view()),
    path('<int:user_id>/change_password/', views.ChangePasswordView.as_view()),
    path('', views.UserList.as_view()),
    path('<int:user_id>/', views.UserDetail.as_view()),
    path('get_id/', views.GetUserID.as_view()),
    path('notification/', views.NotificationList.as_view()),
    path('notification/<int:notify_id>/', views.NotificationDetail.as_view()),
]