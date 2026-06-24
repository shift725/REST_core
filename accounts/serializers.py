from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """使用者序列化器"""

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'phone', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserRegisterSerializer(serializers.ModelSerializer):
    """使用者註冊序列化器"""

    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=CustomUser.objects.all(), message='此 email 已被註冊')]
    )
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=CustomUser.objects.all(), message='此帳號已被使用')]
    )
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password_confirm', 'phone']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': '密碼不一致'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    自訂 Token 序列化器
    在 JWT payload 中加入額外的使用者資訊
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 在 token 中加入自訂資料
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['is_staff'] = user.is_staff

        return token

    def validate(self, attrs):
        """驗證並回傳額外資訊"""
        data = super().validate(attrs)

        # 在回應中加入使用者資訊（不在 token 內，僅回應時附帶）
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
        }

        return data
