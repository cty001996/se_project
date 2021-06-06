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
    path('read_notification/<int:notify_id>/', views.ReadNotification.as_view()),
    path('verify_email/<slug:uidb64>/<slug:token>/', views.EmailVerification.as_view(), name='email_verify'),
    path('password_reset/<slug:uidb64>/<slug:token>/', views.PasswordReset.as_view(), name='password_reset'),
    path('forget_password/', views.ForgetPassword.as_view()),
    path('send_verify_mail/', views.SendVerifyMail.as_view()),
]