from django.http import Http404
from django.urls import reverse
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser, Notification
from .serializers import ChangePasswordSerializer, UserEditSerializer, UserCreateSerializer, NotificationSerializer, \
    NotifyEditSerializer
from rest_framework.permissions import AllowAny

from django.core.mail import EmailMessage

from django.utils.encoding import force_bytes, force_text, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from .utils import token_generator

from .permissions import IsVerify


def send_verify_mail(request, user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
    domain = 'ntu-online-group.herokuapp.com'
    token = token_generator.make_token(user)
    user.is_verify = False
    user.save()
    link = f"/verify-mail/{uidb64}/{token}/"
    url = 'https://' + domain + link
    email_subject = '[Online Group] 驗證信'
    email_body = f'{user.username}你好，以下是驗證連結 {url}'
    email = EmailMessage(
        email_subject,
        email_body,
        'noreply@ntu.edu.tw',
        [user.email],
    )
    email.send()


def send_reset_mail(request, user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
    domain = 'ntu-online-group.herokuapp.com'
    token = token_generator.make_token(user)
    link = f"/forgetpwd/{uidb64}/{token}/"
    url = 'https://' + domain + link
    email_subject = '[Online Group] 重設密碼'
    email_body = f'{user.username}你好，以下是重設密碼連結 {url}'
    email = EmailMessage(
        email_subject,
        email_body,
        'noreply@ntu.edu.tw',
        [user.email],
    )
    email.send()


class Register(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                send_verify_mail(request, user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def get_object(self, user_id):
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise Http404

    def put(self, request, user_id):
        user = self.get_object(user_id)
        if user != request.user:
            return Response({"error": "You can only change your password"}, status=status.HTTP_403_FORBIDDEN)
        password = request.data["old_password"]
        if not user.check_password(password):
            return Response({"error": "old password is not correct"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ChangePasswordSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserList(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def get(self, request):
        users = CustomUser.objects.all()
        serializer = UserCreateSerializer(users, many=True)
        return Response(serializer.data)


class UserDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, user_id):
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            raise Http404

    def get(self, request, user_id):
        user = self.get_object(user_id)
        serializer = UserCreateSerializer(user)
        return Response(serializer.data)

    def put(self, request, user_id):
        user = self.get_object(user_id)
        origin_mail = user.email
        if user != request.user:
            return Response({"error": "You can only edit yourself profile"}, status=status.HTTP_403_FORBIDDEN)
        serializer = UserEditSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            if origin_mail != user.email:
                send_verify_mail(request, user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetUserID(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"id": request.user.id})


class NotificationList(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def get(self, request):
        serializer = NotificationSerializer(request.user.notifications, many=True)
        return Response(serializer.data)


class NotificationDetail(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def delete(self, request, notify_id):
        if not Notification.objects.filter(id=notify_id, user=request.user).exists():
            return Response({"error": "notification id does not exist or it does not belong to you"},
                            status=status.HTTP_400_BAD_REQUEST)

        removal = Notification.objects.get(id=notify_id, user=request.user)
        removal.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmailVerification(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        if user is not None and token_generator.check_token(user, token):
            user.is_verify = True
            user.save()
            return Response("success")
        else:
            # invalid link
            return Response("failed", status=status.HTTP_400_BAD_REQUEST)


class PasswordReset(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        if user is not None and token_generator.check_token(user, token):
            if not "password" in request.data:
                return Response({"error": "must contain password field"}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(request.data["password"])
            return Response("success")
        return Response("error", status=status.HTTP_400_BAD_REQUEST)


class ForgetPassword(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', None)
        if not CustomUser.objects.filter(email=email).exists():
            return Response({"error": "The email does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        user = CustomUser.objects.get(email=email)
        send_reset_mail(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SendVerifyMail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        send_verify_mail(request, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReadNotification(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerify]

    def put(self, request, notify_id):
        if not Notification.objects.filter(id=notify_id, user=request.user).exists():
            return Response({"error": "notification id does not exist or it does not belong to you"},
                            status=status.HTTP_400_BAD_REQUEST)
        notice = Notification.objects.get(id=notify_id, user=request.user)
        notice.status = "read"
        notice.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
