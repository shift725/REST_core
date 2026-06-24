from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import (
    CustomTokenObtainPairView,
    LogoutView,
    UserDetailView,
    UserListView,
    UserRegisterView,
)

app_name = 'auth'

urlpatterns = [
    # 認證相關
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    # Token 管理
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # 使用者資料
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/<uuid:pk>/', UserDetailView.as_view(), name='user_detail'),
]
