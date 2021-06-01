from rest_framework import serializers
from user.models import CustomUser, Notification


class UserCreateSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'password', 'password2', 'last_name', 'first_name', 'department', 'nickname')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        password2 = validated_data.pop('password2', None)
        if validated_data["email"].split("@")[1] != "ntu.edu.tw":
            raise serializers.ValidationError({"email": "Must be NTU mail"})
        instance = self.Meta.model(**validated_data)
        if password is not None:
            if password == password2:
                instance.set_password(password)
            else:
                raise serializers.ValidationError({"password": "Password fields didn't match."})
        instance.save()
        return instance


class UserEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ('last_name', 'first_name', 'department', 'email', 'nickname')


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('old_password', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
