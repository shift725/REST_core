from django.db import IntegrityError
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import CustomUser
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegisterSerializer,
    UserSerializer,
)


class UserRegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — 註冊成功後直接回傳 user 與 JWT。"""

    queryset = CustomUser.objects.all()
    serializer_class = UserRegisterSerializer
    # authentication_classes 清空：避免殘留過期 token 讓 JWTAuthentication 先拋 401 擋下公開端點。
    authentication_classes = []
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
        except IntegrityError:
            # UniqueValidator 通過後若有並行請求搶先註冊，DB unique 限制在此擋下 → 409 而非 500。
            return Response(
                {'error': '帳號或 email 已被使用'},
                status=status.HTTP_409_CONFLICT,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'message': '註冊成功',
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'patch']  # 只開放 GET/PATCH

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdminUser()]


class CustomTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/login/ — 以 email + password 換取 JWT，回應附帶 user。"""

    serializer_class = CustomTokenObtainPairSerializer
    # 同註冊：登入時還沒有 token，不該因 header 殘留的過期 token 被 JWTAuthentication 擋下。
    authentication_classes = []
    permission_classes = [AllowAny]


class LogoutView(APIView):
    """POST /api/auth/logout/ — 將傳入的 refresh token 加入黑名單。"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            RefreshToken(request.data.get('refresh')).blacklist()
            return Response({'message': '登出成功'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({'error': '無效的 token'}, status=status.HTTP_400_BAD_REQUEST)
