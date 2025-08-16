from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import models

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken


from .models import CustomUser


class UserCreationSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password_confirm']
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True}
        }

    def _validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        attrs['password'] = self._validate_password(attrs['password'])
        return super().validate(attrs)

    def create(self, validated_data: dict):
        # validated_data['is_active'] = False
        password = validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(
            **validated_data
        )
        return user


class UserChangeSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email']
        extra_kwargs = {
            'email': {'required': False},
            'username': {'required': False}
        }

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be updated")
        if  CustomUser.objects.filter(
            models.Q(username=attrs.get('username')) | models.Q(email=attrs.get('email'))
            ).exists():
            raise serializers.ValidationError("Username or email already exists")

        return super().validate(attrs)


class UserSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email']
        read_only_fields = ['id', ]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'username_or_email'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username_or_email'] = serializers.CharField(
            write_only=True, required=True, label='Username or Email'
        )

        self.fields['username_or_email'] = serializers.CharField(
            write_only=True,
            required=True,
            label='Username or Email'
        )

    def validate(self, attrs):
        username_or_email = attrs.get(self.username_field)
        password = attrs.get('password')
        if not username_or_email or not password:
            raise serializers.ValidationError(
                "Both username/email and password are required")
        user = CustomUser.objects.filter(
            models.Q(username=username_or_email) | models.Q(
                email=username_or_email)
        ).first()

        if user is None or not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_active:
            raise serializers.ValidationError("User account is inactive")

        self.username_field = 'username'
        attrs['username'] = user.username
        data = super().validate(attrs)

        data['user'] = UserSerializer(user).data  # type:ignore
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except Exception as e:
            raise serializers.ValidationError("Invalid token") from e
        return True
